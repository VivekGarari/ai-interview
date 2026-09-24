import unittest
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.question import Question, QuestionDifficulty, QuestionType
from app.models.session import InterviewType, SessionQuestion
from app.models.users import User
from app.routers.interview import _get_initial_question_text, start_session
from app.schemas.interview import StartSessionRequest


class InterviewQuestionSelectionTests(unittest.TestCase):
    def test_explicit_topic_uses_persistent_question_without_ai(self):
        db = Mock()
        stored_question = Mock(content="Stored question")

        with patch(
            "app.routers.interview.get_random_question",
            return_value=stored_question,
        ) as get_random, patch.object(
            __import__("app.routers.interview", fromlist=["ai_service"]).ai_service,
            "generate_question",
        ) as generate_question:
            text = _get_initial_question_text(
                db, "topic-id", "backend engineer", "technical", "hard"
            )

        self.assertEqual(text, "Stored question")
        get_random.assert_called_once_with(
            db, topic_id="topic-id", difficulty="hard"
        )
        generate_question.assert_not_called()

    def test_explicit_topic_without_match_uses_ai_fallback(self):
        db = Mock()

        with patch(
            "app.routers.interview.get_random_question", return_value=None
        ), patch.object(
            __import__("app.routers.interview", fromlist=["ai_service"]).ai_service,
            "generate_question",
            return_value="AI question",
        ) as generate_question:
            text = _get_initial_question_text(
                db, "topic-id", "backend engineer", "technical", "medium"
            )

        self.assertEqual(text, "AI question")
        generate_question.assert_called_once_with(
            role="backend engineer",
            interview_type="technical",
            history=[],
            difficulty="medium",
        )

    def test_without_topic_uses_existing_ai_behavior(self):
        db = Mock()

        with patch("app.routers.interview.get_random_question") as get_random, patch.object(
            __import__("app.routers.interview", fromlist=["ai_service"]).ai_service,
            "generate_question",
            return_value="AI question",
        ) as generate_question:
            text = _get_initial_question_text(
                db, None, "backend engineer", "technical", "medium"
            )

        self.assertEqual(text, "AI question")
        get_random.assert_not_called()
        generate_question.assert_called_once()

    def test_start_persists_selected_question_in_session_question(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        db = Session(engine)
        user = User(
            email="candidate@example.com",
            hashed_password="hashed",
            full_name="Candidate",
        )
        db.add(user)
        db.commit()

        with patch(
            "app.routers.interview.ai_service.generate_question",
            return_value="AI question",
        ):
            response = start_session(
                StartSessionRequest(
                    interview_type=InterviewType.TECHNICAL,
                    target_role="backend engineer",
                    difficulty="medium",
                ),
                db,
                user,
            )

        persisted = db.query(SessionQuestion).one()
        self.assertEqual(response["question"]["question_text"], "AI question")
        self.assertEqual(persisted.question_text, "AI question")
        db.close()


if __name__ == "__main__":
    unittest.main()