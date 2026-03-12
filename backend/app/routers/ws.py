from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.users import User
from app.models.session import InterviewSession, SessionQuestion, SessionStatus
from app.services.ai_service import ai_service
from datetime import datetime, timezone

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/interview/{session_id}")
async def interview_websocket(websocket: WebSocket, session_id: str):
    """
    Real-time WebSocket for interview sessions.
    
    Client sends:  { "type": "answer", "question_id": "...", "answer": "..." }
    Server sends:  { "type": "feedback", "score": 8, "feedback": "...", "next_question": {...} }
    """
    await websocket.accept()
    db: Session = SessionLocal()

    try:
        # Step 1: Authenticate via token sent in first message
        auth_msg = await websocket.receive_text()
        auth_data = json.loads(auth_msg)

        token = auth_data.get("token")
        user_id = decode_token(token, expected_type="access")

        if not user_id:
            await websocket.send_text(json.dumps({"type": "error", "message": "Unauthorized"}))
            await websocket.close()
            return

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.send_text(json.dumps({"type": "error", "message": "User not found"}))
            await websocket.close()
            return

        # Step 2: Verify session
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        ).first()

        if not session:
            await websocket.send_text(json.dumps({"type": "error", "message": "Session not found"}))
            await websocket.close()
            return

        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": f"Connected to interview session {session_id}",
            "session": {
                "id": session.id,
                "type": session.interview_type.value,
                "role": session.target_role,
            }
        }))

        # Step 3: Main message loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "answer":
                question_id = message.get("question_id")
                answer_text = message.get("answer", "")

                # Get question
                question = db.query(SessionQuestion).filter(
                    SessionQuestion.id == question_id,
                    SessionQuestion.session_id == session_id,
                ).first()

                if not question:
                    await websocket.send_text(json.dumps({
                        "type": "error", "message": "Question not found"
                    }))
                    continue

                # Save answer
                question.answer_text = answer_text
                question.answered_at = datetime.now(timezone.utc)

                # Stream back: "thinking" indicator
                await websocket.send_text(json.dumps({"type": "thinking"}))

                # AI evaluation
                evaluation = ai_service.evaluate_answer(
                    question=question.question_text,
                    answer=answer_text,
                    role=session.target_role,
                    interview_type=session.interview_type.value,
                )

                question.score = evaluation["score"]
                question.ai_feedback = evaluation["feedback"]

                # Check if session should continue
                answered_count = db.query(SessionQuestion).filter(
                    SessionQuestion.session_id == session_id,
                    SessionQuestion.answer_text.isnot(None),
                ).count()

                next_question = None
                if answered_count < 5:
                    history = [q.question_text for q in db.query(SessionQuestion).filter(
                        SessionQuestion.session_id == session_id
                    ).all()]

                    next_q_text = ai_service.generate_question(
                        role=session.target_role,
                        interview_type=session.interview_type.value,
                        history=history,
                        difficulty=session.difficulty,
                    )

                    next_q = SessionQuestion(
                        session_id=session.id,
                        order_index=answered_count + 2,
                        question_text=next_q_text,
                    )
                    db.add(next_q)
                    db.flush()
                    next_question = {
                        "id": next_q.id,
                        "question_text": next_q.question_text,
                        "order_index": next_q.order_index,
                    }

                db.commit()

                await websocket.send_text(json.dumps({
                    "type": "feedback",
                    "score": evaluation["score"],
                    "feedback": evaluation["feedback"],
                    "follow_up": evaluation.get("follow_up"),
                    "next_question": next_question,
                    "session_complete": next_question is None,
                    "questions_answered": answered_count,
                }))

            elif msg_type == "end":
                await websocket.send_text(json.dumps({
                    "type": "session_ended",
                    "message": "Use POST /interview/end to get your full report."
                }))
                break

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
    finally:
        db.close()