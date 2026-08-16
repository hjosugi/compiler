from __future__ import annotations

import heapq
from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class Interval:
    start: int
    end: int
    value: str


@dataclass(frozen=True, slots=True)
class Allocation:
    value: str
    location: str


def allocate(intervals: list[Interval], registers: tuple[str, ...]) -> list[Allocation]:
    """Allocate live intervals with a deterministic linear-scan allocator."""
    free = list(registers)
    active: list[tuple[int, str, str]] = []
    result: list[Allocation] = []
    spill_slot = 0

    for interval in sorted(intervals):
        while active and active[0][0] < interval.start:
            _, _, register = heapq.heappop(active)
            free.append(register)
            free.sort()

        if free:
            register = free.pop(0)
            heapq.heappush(active, (interval.end, interval.value, register))
            result.append(Allocation(interval.value, register))
            continue

        spill_end, spill_value, spill_register = max(active)
        if spill_end > interval.end:
            active.remove((spill_end, spill_value, spill_register))
            heapq.heapify(active)
            previous = next(i for i, item in enumerate(result) if item.value == spill_value)
            result[previous] = Allocation(spill_value, f"stack[{spill_slot}]")
            spill_slot += 1
            heapq.heappush(active, (interval.end, interval.value, spill_register))
            result.append(Allocation(interval.value, spill_register))
        else:
            result.append(Allocation(interval.value, f"stack[{spill_slot}]"))
            spill_slot += 1
    return result


def main() -> None:
    intervals = [
        Interval(0, 8, "a"),
        Interval(1, 3, "b"),
        Interval(2, 6, "c"),
        Interval(4, 5, "d"),
    ]
    for item in allocate(intervals, ("r0", "r1")):
        print(f"{item.value} -> {item.location}")


if __name__ == "__main__":
    main()
