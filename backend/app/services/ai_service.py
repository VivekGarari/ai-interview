import json
from groq import Groq
from app.core.config import settings


class AIService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.AI_MODEL

    def _chat(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()

    def generate_question(self, role: str, interview_type: str, history: list[str], difficulty: str = "medium") -> str:
        history_text = "\n".join(history[-4:]) if history else "No previous questions."
        system = f"""You are an expert interviewer conducting a {interview_type} interview
for a {role} position. Ask one focused, relevant question at a time.
Difficulty level: {difficulty}. Be professional and realistic.
Do not number the question. Just ask it directly."""
        user = f"""Previous questions asked:
{history_text}

Generate the next interview question. Return ONLY the question, nothing else."""
        return self._chat(system, user)

    def evaluate_answer(self, question: str, answer: str, role: str, interview_type: str) -> dict:
        system = f"""You are an expert interviewer evaluating answers for a {role} position.
Be honest, constructive, and specific in your feedback."""
        user = f"""Question: {question}

Candidate's Answer: {answer}

Evaluate this answer and respond in this exact format:
SCORE: [0-10]
FEEDBACK: [2-3 sentences of constructive feedback]
FOLLOW_UP: [One follow-up question to dig deeper, or "None" if answer was complete]"""
        response = self._chat(system, user)
        score = 5.0
        feedback = "Good attempt."
        follow_up = None
        for line in response.strip().split("\n"):
            if line.startswith("SCORE:"):
                try:
                    score = float(line.replace("SCORE:", "").strip())
                except ValueError:
                    score = 5.0
            elif line.startswith("FEEDBACK:"):
                feedback = line.replace("FEEDBACK:", "").strip()
            elif line.startswith("FOLLOW_UP:"):
                fu = line.replace("FOLLOW_UP:", "").strip()
                follow_up = None if fu.lower() == "none" else fu
        return {"score": score, "feedback": feedback, "follow_up": follow_up}

    def generate_feedback_report(self, session_data: dict) -> dict:
        questions_summary = "\n".join([
            f"Q: {q['question']}\nA: {q['answer']}\nScore: {q['score']}/10"
            for q in session_data.get("questions", [])
        ])
        system = """You are an expert career coach providing detailed interview feedback.
Be encouraging but honest. Focus on actionable improvements."""
        user = f"""Interview Type: {session_data.get('interview_type')}
Role: {session_data.get('role')}

Questions and Answers:
{questions_summary}

Provide a final report in this exact format:
SUMMARY: [2-3 sentence overall assessment]
STRENGTHS: [strength1] | [strength2] | [strength3]
IMPROVEMENTS: [improvement1] | [improvement2] | [improvement3]
OVERALL_SCORE: [0-10]"""
        response = self._chat(system, user)
        result = {"summary": "", "strengths": [], "improvements": [], "overall_score": 5.0}
        for line in response.strip().split("\n"):
            if line.startswith("SUMMARY:"):
                result["summary"] = line.replace("SUMMARY:", "").strip()
            elif line.startswith("STRENGTHS:"):
                result["strengths"] = [s.strip() for s in line.replace("STRENGTHS:", "").split("|")]
            elif line.startswith("IMPROVEMENTS:"):
                result["improvements"] = [s.strip() for s in line.replace("IMPROVEMENTS:", "").split("|")]
            elif line.startswith("OVERALL_SCORE:"):
                try:
                    result["overall_score"] = float(line.replace("OVERALL_SCORE:", "").strip())
                except ValueError:
                    result["overall_score"] = 5.0
        return result

    def generate_exam_questions(self, topic: str, role: str, difficulty: str, num_questions: int, question_types: list[str]) -> list[dict]:
        types_str = ", ".join(question_types)
        prompt = f"""Generate exactly {num_questions} exam questions for a {role} candidate on the topic: "{topic}".
Difficulty: {difficulty}
Question types to include (mix them): {types_str}

Return ONLY a JSON array. Each question object must have:
- "type": one of {question_types}
- "question": the question text
- "correct_answer": the correct answer (for MCQ: just the letter like "A", for others: full answer)
- "explanation": brief explanation of the correct answer
- "points": 1 for mcq, 1 for short_answer, 2 for coding

For MCQ questions also include:
- "options": list of exactly 4 strings like ["A. option1", "B. option2", "C. option3", "D. option4"]

Return ONLY the JSON array, no markdown, no extra text."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except Exception:
            return [{"type": "short_answer", "question": f"Explain {topic} in the context of {role}.", "correct_answer": "Varies", "explanation": "Open ended.", "points": 1}]

    def grade_exam_answer(self, question: str, user_answer: str, correct_answer: str, question_type: str, role: str) -> dict:
        prompt = f"""You are grading a {question_type} answer for a {role} candidate.

Question: {question}
Expected answer: {correct_answer}
Student answer: {user_answer}

Grade this answer from 0-10 based on correctness, completeness, and clarity.
Return ONLY a JSON object:
{{"score": <0-10>, "feedback": "<1-2 sentence feedback>"}}"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except Exception:
            return {"score": 5, "feedback": "Could not evaluate automatically."}

    def generate_exam_summary(self, topic: str, role: str, percentage: float, question_results: list[dict]) -> dict:
        correct = sum(1 for r in question_results if r["correct"])
        total = len(question_results)
        wrong_questions = [r["question"][:60] for r in question_results if not r["correct"]][:5]
        prompt = f"""A {role} candidate scored {percentage}% ({correct}/{total}) on a "{topic}" exam.
Questions they got wrong: {wrong_questions}

Return ONLY a JSON object:
{{
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"],
  "recommendation": "<1-2 sentence study recommendation>"
}}"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except Exception:
            return {"strengths": [], "weaknesses": [], "recommendation": "Keep practicing!"}


ai_service = AIService()