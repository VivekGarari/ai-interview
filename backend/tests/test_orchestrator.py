import unittest

from app.services.orchestrator import AIOrchestrator


class AIOrchestratorTests(unittest.TestCase):
    def test_selects_groq_for_coding_tasks_by_default(self):
        orchestrator = AIOrchestrator()
        provider = orchestrator.select_provider("coding", {"groq": True})
        self.assertEqual(provider, "groq")

    def test_selects_openai_for_reasoning_tasks_when_available(self):
        orchestrator = AIOrchestrator()
        provider = orchestrator.select_provider("reasoning", {"openai": True, "groq": True})
        self.assertEqual(provider, "openai")

    def test_reports_capabilities_without_exposing_private_details(self):
        orchestrator = AIOrchestrator()
        capabilities = orchestrator.get_capabilities()
        self.assertIn("llm", capabilities)
        self.assertIn("search", capabilities)
        self.assertIn("memory", capabilities)
        self.assertIn("automation", capabilities)


if __name__ == "__main__":
    unittest.main()
