import json
import os
import tempfile
import unittest
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pipeline

class SourceRegistryTests(unittest.TestCase):
    def test_reserves_sources_and_persists_across_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "source_usage.json")
            with patch.object(pipeline, "SOURCE_REGISTRY_FILE", path):
                pipeline.reserve_sources(["/clips/unique-a.mp4", "/clips/unique-b.mp4"])
                self.assertIn("unique-a.mp4", pipeline.load_used_sources())
                with self.assertRaises(SystemExit):
                    pipeline.reserve_sources(["/other/unique-a.mp4"])

    def test_rejects_repeated_source_in_one_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "source_usage.json")
            with patch.object(pipeline, "SOURCE_REGISTRY_FILE", path):
                with self.assertRaises(SystemExit):
                    pipeline.reserve_sources(["/clips/a.mp4", "/clips/a.mp4"])

if __name__ == "__main__":
    unittest.main()
