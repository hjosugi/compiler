from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Node:
    op: str
    args: tuple[Node | str | int, ...]


@dataclass(frozen=True, slots=True)
class Selection:
    cost: int
    instructions: tuple[str, ...]
    result: str


class Selector:
    """A small bottom-up dynamic-programming instruction selector."""

    def __init__(self) -> None:
        self.next_temp = 0

    def temp(self) -> str:
        value = f"v{self.next_temp}"
        self.next_temp += 1
        return value

    def select(self, value: Node | str | int) -> Selection:
        if isinstance(value, str):
            return Selection(0, (), value)
        if isinstance(value, int):
            target = self.temp()
            return Selection(1, (f"MOV {target}, {value}",), target)

        selected = [self.select(arg) for arg in value.args]
        instructions = tuple(line for item in selected for line in item.instructions)
        target = self.temp()
        if value.op == "add":
            left, right = selected
            # A target with a three-address add can keep both inputs unchanged.
            return Selection(
                left.cost + right.cost + 1,
                instructions + (f"ADD {target}, {left.result}, {right.result}",),
                target,
            )
        if value.op == "mul":
            left, right = selected
            if isinstance(value.args[1], int) and value.args[1] in {2, 4, 8}:
                shift = {2: 1, 4: 2, 8: 3}[value.args[1]]
                # This target-specific rule is cheaper than a general multiply.
                return Selection(
                    left.cost + 1,
                    left.instructions + (f"SHL {target}, {left.result}, {shift}",),
                    target,
                )
            return Selection(
                left.cost + right.cost + 3,
                instructions + (f"MUL {target}, {left.result}, {right.result}",),
                target,
            )
        raise ValueError(f"unsupported node: {value.op}")


def main() -> None:
    expression = Node("mul", (Node("add", ("a", "b")), 8))
    selection = Selector().select(expression)
    print(f"cost = {selection.cost}")
    print("\n".join(selection.instructions))


if __name__ == "__main__":
    main()

