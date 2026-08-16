from __future__ import annotations

import unittest

from runner import sha256_bytes, summarize


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


if __name__ == "__main__":
    unittest.main()
