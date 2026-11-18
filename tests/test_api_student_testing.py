"""End-to-end API check against the local student-testing trip folders."""

import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src.api import app as api


class StudentTestingApiTest(unittest.TestCase):
    def test_all_available_student_trips(self):
        data_dir = os.getenv("PATHSNAP_STUDENT_TEST_DIR")
        if not data_dir:
            self.skipTest("Set PATHSNAP_STUDENT_TEST_DIR to the trip-folder parent")
        api.DATA_DIR = Path(data_dir)
        self.assertTrue(api.DATA_DIR.is_dir())
        self.assertTrue(api.MODEL_PATH.is_file())
        client = TestClient(api.app)
        trip_ids = client.get("/trips").json()["trip_ids"]
        self.assertTrue(trip_ids, "No student-testing trips found")
        for trip_id in trip_ids:
            with self.subTest(trip_id=trip_id):
                response = client.post("/predict", json={"trip_id": trip_id})
                self.assertEqual(response.status_code, 200, response.text)
                result = response.json()
                self.assertEqual(result["trip_id"], trip_id)
                self.assertEqual(len(result["predicted_arc_ids"]), result["diagnostics"]["observations"])
                self.assertTrue(all(isinstance(arc_id, int) for arc_id in result["predicted_arc_ids"]))
                self.assertGreaterEqual(result["accuracy"], 0)
                self.assertLessEqual(result["accuracy"], 1)
                self.assertNotIn("reference", response.text.lower())
                self.assertNotIn("actual_route", response.text.lower())


if __name__ == "__main__":
    unittest.main()
