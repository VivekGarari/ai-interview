import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.question import (
    Domain,
    Question,
    QuestionDifficulty,
    QuestionType,
    Subtopic,
    Topic,
)
from app.services.question_service import (
    create_question,
    get_questions_by_topic,
    get_random_question,
)


class QuestionServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)

    def setUp(self):
        self.db = Session(self.engine)
        self.domain = Domain(name="Backend")
        self.topic = Topic(name="APIs", domain=self.domain)
        self.other_topic = Topic(name="Databases", domain=self.domain)
        self.subtopic = Subtopic(name="FastAPI", topic=self.topic)
        self.other_subtopic = Subtopic(name="PostgreSQL", topic=self.other_topic)
        self.db.add(self.domain)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        with self.engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())

    def test_create_question_persists_question(self):
        question = create_question(
            self.db,
            "What is dependency injection?",
            QuestionDifficulty.MEDIUM,
            QuestionType.THEORY,
            self.subtopic.id,
        )

        self.assertIsNotNone(question.id)
        self.assertEqual(question.content, "What is dependency injection?")
        self.assertEqual(question.subtopic_id, self.subtopic.id)
        self.assertEqual(question.difficulty, QuestionDifficulty.MEDIUM)
        self.assertEqual(question.type, QuestionType.THEORY)

    def test_create_question_with_model_answer_creates_version(self):
        question = create_question(
            self.db,
            "Explain REST.",
            "easy",
            "theory",
            self.subtopic.id,
            model_answer="REST uses resource-oriented HTTP semantics.",
        )

        self.assertEqual(len(question.versions), 1)
        self.assertEqual(question.versions[0].content, question.content)
        self.assertEqual(
            question.versions[0].model_answer,
            "REST uses resource-oriented HTTP semantics.",
        )

    def test_create_question_with_invalid_subtopic_fails(self):
        with self.assertRaisesRegex(ValueError, "Subtopic not found"):
            create_question(
                self.db,
                "Question",
                "easy",
                "theory",
                "missing-subtopic",
            )

    def test_get_questions_by_topic_returns_matching_topic_questions(self):
        question = create_question(
            self.db, "API question", "medium", "theory", self.subtopic.id
        )
        create_question(
            self.db, "Database question", "medium", "theory", self.other_subtopic.id
        )

        questions = get_questions_by_topic(self.db, self.topic.id)

        self.assertEqual([item.id for item in questions], [question.id])

    def test_get_questions_by_topic_excludes_other_topic(self):
        create_question(self.db, "API question", "medium", "theory", self.subtopic.id)
        other_question = create_question(
            self.db, "Database question", "medium", "theory", self.other_subtopic.id
        )

        questions = get_questions_by_topic(self.db, self.topic.id)

        self.assertNotIn(other_question.id, [item.id for item in questions])

    def test_get_questions_by_topic_filters_difficulty(self):
        easy = create_question(self.db, "Easy", "easy", "theory", self.subtopic.id)
        create_question(self.db, "Hard", "hard", "theory", self.subtopic.id)

        questions = get_questions_by_topic(self.db, self.topic.id, difficulty="easy")

        self.assertEqual([item.id for item in questions], [easy.id])

    def test_get_questions_by_topic_filters_question_type(self):
        coding = create_question(self.db, "Coding", "medium", "coding", self.subtopic.id)
        create_question(self.db, "Theory", "medium", "theory", self.subtopic.id)

        questions = get_questions_by_topic(self.db, self.topic.id, question_type="coding")

        self.assertEqual([item.id for item in questions], [coding.id])

    def test_get_random_question_returns_matching_question(self):
        question = create_question(
            self.db, "Coding", "hard", "coding", self.subtopic.id
        )

        result = get_random_question(
            self.db, self.topic.id, difficulty="hard", question_type="coding"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.id, question.id)

    def test_get_random_question_returns_none_when_no_match_exists(self):
        result = get_random_question(self.db, self.topic.id, difficulty="hard")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()