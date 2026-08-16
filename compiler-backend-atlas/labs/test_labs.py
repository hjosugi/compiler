from __future__ import annotations

import unittest

from dominators import compute_dominators
from instruction_selection import Node, Selector
from linear_scan import Interval, allocate


class CompilerLabTests(unittest.TestCase):
    def test_diamond_dominators(self) -> None:
        cfg = {
            "entry": ("left", "right"),
            "left": ("merge",),
            "right": ("merge",),
            "merge": (),
        }
        result = compute_dominators("entry", cfg)
        self.assertEqual(result["merge"], {"entry", "merge"})

    def test_linear_scan_spills(self) -> None:
        intervals = [Interval(0, 5, "a"), Interval(1, 4, "b")]
        result = allocate(intervals, ("r0",))
        locations = {item.value: item.location for item in result}
        self.assertEqual(set(locations), {"a", "b"})
        self.assertTrue(any(location.startswith("stack") for location in locations.values()))

    def test_instruction_selector_uses_shift_for_power_of_two(self) -> None:
        result = Selector().select(Node("mul", ("value", 8)))
        self.assertEqual(result.instructions, ("SHL v1, value, 3",))


if __name__ == "__main__":
    unittest.main()

