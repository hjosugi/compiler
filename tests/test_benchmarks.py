from __future__ import annotations

import json
import unittest
from pathlib import Path

from benchmarks.runner import SCHEMA, sha256_bytes, summarize

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkHelpersTests(unittest.TestCase):
    def test_summary_uses_median(self) -> None:
        result = summarize([9.0, 1.0, 3.0])
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["median_seconds"], 3.0)

    def test_sha256_is_stable(self) -> None:
        self.assertEqual(
            sha256_bytes(b"kofu"),
            "cb68833f0c9ed75ea6d3800d5e399dc70b5809cfc0c2013a764bc3365763b8c0",
        )

    def test_empty_samples_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            summarize([])

    def test_runner_and_json_schema_use_the_same_protocol(self) -> None:
        schema = json.loads((ROOT / "benchmarks" / "schema.json").read_text())
        self.assertEqual(schema["properties"]["schema"]["const"], SCHEMA)


if __name__ == "__main__":
    unittest.main()
