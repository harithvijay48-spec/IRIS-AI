import unittest

from fastapi.testclient import TestClient

from main import app


class ApiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_does_not_return_credentials(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertIn("providers", payload)
        self.assertNotIn("MODEL_API_KEY", str(payload))

    def test_frontend_is_served_by_backend(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("IRIS", response.text)

    def test_short_question_is_rejected(self):
        response = self.client.post("/api/check", json={"question": "  "})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
