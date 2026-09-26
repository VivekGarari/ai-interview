import unittest
import asyncio
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.security import get_current_user
from app.models.session import InterviewSession, InterviewType, SessionQuestion
from app.models.users import User
from app.routers.auth import login, refresh_tokens, signup, verify_email
from app.routers.exam import _exams, submit_exam
from app.routers.video import get_question_audio, router as video_router
from app.routers.ws import interview_websocket
from app.schemas.auth import LoginRequest, RefreshRequest, SignupRequest, VerifyEmailRequest
from app.schemas.exam import ExamSubmission, QuestionAnswer


class FakeWebSocket:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []
        self.closed = False

    async def accept(self):
        pass

    async def receive_text(self):
        return self.messages.pop(0)

    async def send_text(self, message):
        self.sent.append(json.loads(message))

    async def close(self):
        self.closed = True


class FakeWebSocketQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args):
        return self

    def first(self):
        return self.result


class FakeWebSocketDB:
    def __init__(self, user, session=None):
        self.user = user
        self.session = session

    def query(self, model):
        return FakeWebSocketQuery(self.user if model is User else self.session)

    def close(self):
        pass


class SecurityRemediationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)

    def setUp(self):
        self.db = Session(self.engine)
        _exams.clear()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        with self.engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
        _exams.clear()

    def add_user(self, email, is_verified=True):
        user = User(
            email=email,
            hashed_password="not-used",
            full_name=email.split("@")[0],
            is_verified=is_verified,
        )
        self.db.add(user)
        self.db.commit()
        return user

    def test_exam_owner_can_submit_and_other_user_cannot(self):
        owner = SimpleNamespace(id="owner-id")
        other_user = SimpleNamespace(id="other-id")
        _exams["exam-id"] = {
            "config": {"topic": "APIs", "role": "Engineer", "difficulty": "easy"},
            "questions": [
                {
                    "type": "mcq",
                    "question": "What is HTTP?",
                    "correct_answer": "A",
                    "explanation": "A protocol.",
                    "points": 1,
                }
            ],
            "user_id": owner.id,
        }
        submission = ExamSubmission(
            exam_id="exam-id",
            answers=[QuestionAnswer(question_id=0, answer="A")],
        )

        with self.assertRaisesRegex(HTTPException, "Exam not found or expired") as denied:
            submit_exam(submission, other_user)
        self.assertEqual(denied.exception.status_code, 404)
        self.assertIn("exam-id", _exams)

        with patch(
            "app.routers.exam.ai_service.generate_exam_summary",
            return_value={"strengths": [], "weaknesses": [], "recommendation": "Keep practicing."},
        ):
            result = submit_exam(submission, owner)

        self.assertEqual(result.exam_id, "exam-id")
        self.assertNotIn("exam-id", _exams)

    def test_exam_missing_id_remains_safe(self):
        with self.assertRaisesRegex(HTTPException, "Exam not found or expired") as missing:
            submit_exam(
                ExamSubmission(exam_id="missing", answers=[]),
                SimpleNamespace(id="owner-id"),
            )
        self.assertEqual(missing.exception.status_code, 404)

    def test_unverified_refresh_is_rejected(self):
        user = self.add_user("refresh-unverified@example.com", is_verified=False)
        with patch("app.routers.auth.decode_token", return_value=user.id):
            with self.assertRaisesRegex(HTTPException, "verify your email") as denied:
                refresh_tokens(RefreshRequest(refresh_token="refresh"), self.db)
        self.assertEqual(denied.exception.status_code, 403)

    def test_verified_refresh_succeeds(self):
        user = self.add_user("refresh-verified@example.com", is_verified=True)
        with patch("app.routers.auth.decode_token", return_value=user.id), patch(
            "app.routers.auth.create_access_token", return_value="access"
        ), patch("app.routers.auth.create_refresh_token", return_value="refresh"):
            response = refresh_tokens(RefreshRequest(refresh_token="refresh"), self.db)
        self.assertEqual(response.access_token, "access")
        self.assertEqual(response.refresh_token, "refresh")

    def test_invalid_refresh_remains_rejected(self):
        with patch("app.routers.auth.decode_token", return_value=None):
            with self.assertRaisesRegex(HTTPException, "Invalid or expired refresh token") as denied:
                refresh_tokens(RefreshRequest(refresh_token="invalid"), self.db)
        self.assertEqual(denied.exception.status_code, 401)

    def test_video_question_audio_requires_route_authentication(self):
        route = next(
            route for route in video_router.routes
            if getattr(route, "path", "") == "/video/question/{question_id}/audio"
        )
        dependency_calls = [dependency.call for dependency in route.dependant.dependencies]
        from app.core.security import get_current_user as current_user_dependency

        self.assertIn(current_user_dependency, dependency_calls)

    def test_video_question_audio_is_limited_to_session_owner(self):
        owner = self.add_user("owner@example.com")
        other_user = self.add_user("other@example.com")
        interview_session = InterviewSession(
            user_id=owner.id,
            interview_type=InterviewType.TECHNICAL,
            target_role="Engineer",
            difficulty="medium",
        )
        self.db.add(interview_session)
        self.db.flush()
        question = SessionQuestion(
            session_id=interview_session.id,
            order_index=1,
            question_text="Explain HTTP.",
        )
        self.db.add(question)
        self.db.commit()

        with patch(
            "app.routers.video.tts_service.get_question_audio",
            return_value=b"audio",
        ) as generate_audio:
            response = get_question_audio(question.id, self.db, owner)
            self.assertEqual(response.body, b"audio")
            generate_audio.assert_called_once_with("Explain HTTP.")

            with self.assertRaisesRegex(HTTPException, "Question not found") as denied:
                get_question_audio(question.id, self.db, other_user)
            self.assertEqual(denied.exception.status_code, 404)
            self.assertEqual(generate_audio.call_count, 1)

    def test_video_question_audio_missing_question_is_safe(self):
        owner = self.add_user("owner@example.com")
        with patch("app.routers.video.tts_service.get_question_audio") as generate_audio:
            with self.assertRaisesRegex(HTTPException, "Question not found") as missing:
                get_question_audio("missing-question", self.db, owner)
        self.assertEqual(missing.exception.status_code, 404)
        generate_audio.assert_not_called()

    def test_unverified_websocket_user_is_rejected(self):
        websocket = FakeWebSocket([json.dumps({"token": "token"})])
        user = SimpleNamespace(id="user-id", is_verified=False)
        db = FakeWebSocketDB(user)

        with patch("app.routers.ws.decode_token", return_value=user.id), patch(
            "app.routers.ws.SessionLocal", return_value=db
        ):
            asyncio.run(interview_websocket(websocket, "session-id"))

        self.assertTrue(websocket.closed)
        self.assertEqual(websocket.sent, [{"type": "error", "message": "Unauthorized"}])

    def test_verified_websocket_user_can_connect(self):
        websocket = FakeWebSocket([
            json.dumps({"token": "token"}),
            json.dumps({"type": "end"}),
        ])
        user = SimpleNamespace(id="user-id", is_verified=True)
        session = SimpleNamespace(
            id="session-id",
            interview_type=SimpleNamespace(value="technical"),
            target_role="Engineer",
        )
        db = FakeWebSocketDB(user, session)

        with patch("app.routers.ws.decode_token", return_value=user.id), patch(
            "app.routers.ws.SessionLocal", return_value=db
        ):
            asyncio.run(interview_websocket(websocket, "session-id"))

        self.assertEqual(websocket.sent[0]["type"], "connected")
        self.assertEqual(websocket.sent[1]["type"], "session_ended")

    def test_invalid_websocket_token_remains_rejected(self):
        websocket = FakeWebSocket([json.dumps({"token": "invalid"})])
        db = FakeWebSocketDB(None)

        with patch("app.routers.ws.decode_token", return_value=None), patch(
            "app.routers.ws.SessionLocal", return_value=db
        ):
            asyncio.run(interview_websocket(websocket, "session-id"))

        self.assertTrue(websocket.closed)
        self.assertEqual(websocket.sent, [{"type": "error", "message": "Unauthorized"}])

    def test_signup_creates_unverified_user_without_tokens_and_sends_otp(self):
        body = SignupRequest(
            email="new@example.com",
            password="correct horse battery staple",
            full_name="New Candidate",
        )
        with patch("app.services.email_service.email_service.send_otp") as send_otp:
            response = signup(body, self.db)

        user = self.db.execute(select(User).where(User.email == body.email)).scalar_one()
        self.assertFalse(user.is_verified)
        self.assertIsNotNone(user.otp_code)
        self.assertGreater(user.otp_expires_at, datetime.now(timezone.utc).replace(tzinfo=None))
        self.assertFalse(hasattr(response, "access_token"))
        send_otp.assert_called_once_with(user.email, user.full_name, user.otp_code)

    def test_unverified_user_cannot_login_or_use_current_user(self):
        user = self.add_user("unverified@example.com", is_verified=False)
        user.hashed_password = __import__("app.core.security", fromlist=["hash_password"]).hash_password("password123")
        self.db.commit()

        with self.assertRaisesRegex(HTTPException, "verify your email") as denied:
            login(LoginRequest(email=user.email, password="password123"), self.db)
        self.assertEqual(denied.exception.status_code, 403)

        with patch("app.core.security.decode_token", return_value=user.id):
            with self.assertRaises(HTTPException) as current_user_denied:
                get_current_user(SimpleNamespace(credentials="valid-token"), self.db)
        self.assertEqual(current_user_denied.exception.status_code, 401)

    def test_successful_verification_marks_user_verified_and_returns_tokens(self):
        user = self.add_user("verify@example.com", is_verified=False)
        user.otp_code = "123456"
        user.otp_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)
        self.db.commit()

        with patch("app.routers.auth.create_access_token", return_value="access"), patch(
            "app.routers.auth.create_refresh_token", return_value="refresh"
        ):
            response = verify_email(
                VerifyEmailRequest(email=user.email, otp="123456"),
                self.db,
            )

        self.db.refresh(user)
        self.assertTrue(user.is_verified)
        self.assertIsNone(user.otp_code)
        self.assertIsNone(user.otp_expires_at)
        self.assertEqual(response.access_token, "access")
        self.assertEqual(response.refresh_token, "refresh")

    def test_invalid_verification_does_not_change_user(self):
        user = self.add_user("invalid@example.com", is_verified=False)
        user.otp_code = "123456"
        user.otp_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)
        self.db.commit()

        with self.assertRaisesRegex(HTTPException, "Invalid OTP code"):
            verify_email(
                VerifyEmailRequest(email=user.email, otp="654321"),
                self.db,
            )

        self.db.refresh(user)
        self.assertFalse(user.is_verified)
        self.assertEqual(user.otp_code, "123456")

    def test_already_verified_user_gets_safe_verification_error(self):
        user = self.add_user("already-verified@example.com", is_verified=True)

        with self.assertRaisesRegex(HTTPException, "Email already verified") as already_verified:
            verify_email(
                VerifyEmailRequest(email=user.email, otp="123456"),
                self.db,
            )

        self.assertEqual(already_verified.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
