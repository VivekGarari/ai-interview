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

    def generate_coding_problem(self, difficulty: str, topic: str, role: str) -> dict:
        prompt = f"""Generate a coding problem for a {role} candidate.
Topic: {topic}
Difficulty: {difficulty}

Return ONLY a JSON object:
{{
  "title": "<problem title>",
  "description": "<full problem description>",
  "examples": [
    {{"input": "<example input>", "output": "<example output>", "explanation": "<optional>"}}
  ],
  "constraints": ["<constraint 1>", "<constraint 2>"],
  "starter_code": {{
    "python": "<python starter>",
    "javascript": "<js starter>",
    "java": "<java starter>"
  }},
  "solution": "<reference solution in python>",
  "hints": ["<hint 1>", "<hint 2>"]
}}"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except Exception:
            return {
                "title": f"{topic} Problem",
                "description": f"Solve a {difficulty} {topic} problem.",
                "examples": [],
                "constraints": [],
                "starter_code": {"python": "def solution():\n    pass", "javascript": "function solution() {}", "java": ""},
                "solution": "",
                "hints": [],
            }

    def review_code(self, problem: str, code: str, language: str) -> dict:
        prompt = f"""You are an expert code reviewer. Review this {language} solution.

Problem: {problem}

Code:
{code}

Return ONLY a JSON object:
{{
  "score": <0-10>,
  "correct": <true or false>,
  "time_complexity": "<e.g. O(n)>",
  "space_complexity": "<e.g. O(1)>",
  "feedback": "<2-3 sentence review>",
  "improvements": ["<improvement 1>", "<improvement 2>"]
}}"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except Exception:
            return {"score": 5, "correct": False, "time_complexity": "Unknown", "space_complexity": "Unknown", "feedback": "Could not review automatically.", "improvements": []}

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


    def analyze_resume(self, resume_text: str, target_role: str) -> dict:
        """Full resume analysis — scoring, ATS, keywords, section feedback, rewrites."""
        prompt = f"""You are an expert resume reviewer and career coach. Analyze this resume for a {target_role} position.

RESUME TEXT:
{resume_text[:6000]}

Return ONLY a valid JSON object with this exact structure:
{{
  "overall_score": <float 0-10>,
  "ats_score": <float 0-10>,
  "ats_issues": ["<issue1>", "<issue2>"],
  "missing_keywords": ["<keyword1>", "<keyword2>", "<keyword3>", "<keyword4>", "<keyword5>"],
  "section_feedback": [
    {{
      "section": "Summary/Objective",
      "score": <float 0-10>,
      "feedback": "<2 sentence feedback>",
      "rewrite_suggestion": "<improved version or null>"
    }},
    {{
      "section": "Work Experience",
      "score": <float 0-10>,
      "feedback": "<2 sentence feedback>",
      "rewrite_suggestion": "<tip to improve bullet points or null>"
    }},
    {{
      "section": "Skills",
      "score": <float 0-10>,
      "feedback": "<2 sentence feedback>",
      "rewrite_suggestion": "<missing skills to add or null>"
    }},
    {{
      "section": "Education",
      "score": <float 0-10>,
      "feedback": "<1 sentence feedback>",
      "rewrite_suggestion": null
    }}
  ],
  "strengths": ["<strength1>", "<strength2>", "<strength3>"],
  "improvements": ["<improvement1>", "<improvement2>", "<improvement3>"],
  "recommendation": "<2-3 sentence overall recommendation>"
}}

Rules:
- ATS issues = things that make it hard for applicant tracking systems (tables, images, headers, missing keywords, unusual fonts)
- Missing keywords = important skills/terms for {target_role} that are absent from the resume
- Be specific and actionable
- Return ONLY the JSON, no markdown fences"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{{"role": "user", "content": prompt}}],
            temperature=0.4,
            max_tokens=3000,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        import json as _json
        try:
            data = _json.loads(text)
            return data
        except Exception:
            return {{
                "overall_score": 5.0,
                "ats_score": 5.0,
                "ats_issues": ["Could not fully analyze — try again"],
                "missing_keywords": [],
                "section_feedback": [],
                "strengths": [],
                "improvements": ["Please try uploading again"],
                "recommendation": "Analysis failed. Please try again.",
            }}

ai_service = AIService()