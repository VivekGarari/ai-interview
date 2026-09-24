import unittest

from app.routers.ai import RoutingRequest, get_capabilities, route_request


class AIRouterTests(unittest.TestCase):
    def test_get_capabilities_includes_core_layers(self):
        response = get_capabilities()
        self.assertIn("llm", response["capabilities"])
        self.assertIn("search", response["capabilities"])
        self.assertIn("memory", response["capabilities"])

    def test_route_request_selects_openai_for_reasoning(self):
        payload = RoutingRequest(task_type="reasoning", capabilities={"openai": True, "groq": True})
        response = route_request(payload)
        self.assertEqual(response["provider"], "openai")


if __name__ == "__main__":
    unittest.main()
