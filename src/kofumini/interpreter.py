from __future__ import annotations

from dataclasses import dataclass, field

from .errors import RuntimeTrap
from .kir import Instruction, KIRFunction, KIRModule, verify
from .semantics import I64_MAX, I64_MIN


@dataclass(slots=True)
class ExecutionResult:
    return_value: int
    stdout: str


@dataclass(slots=True)
class Interpreter:
    module: KIRModule
    output: list[str] = field(default_factory=list)
    max_call_depth: int = 1_000
    functions: dict[str, KIRFunction] = field(init=False)

    def __post_init__(self) -> None:
        verify(self.module)
        self.functions = {function.name: function for function in self.module.functions}

    def run_main(self) -> ExecutionResult:
        self.output.clear()
        if "main" not in self.functions:
            raise RuntimeTrap("runtime trap: module has no main function")
        value = self.call("main", (), 0)
        return ExecutionResult(int(value), "".join(self.output))

    def call(self, name: str, args: tuple[int | bool, ...], depth: int) -> int | bool:
        if depth > self.max_call_depth:
            raise RuntimeTrap("runtime trap: maximum call depth exceeded")
        function = self.functions.get(name)
        if function is None:
            raise RuntimeTrap(f"runtime trap: unknown function {name}")
        if len(args) != len(function.params):
            raise RuntimeTrap(f"runtime trap: wrong argument count for {name}")
        values: dict[str, int | bool] = {
            param.value: value for param, value in zip(function.params, args, strict=True)
        }
        blocks = {block.label: block for block in function.blocks}
        block = function.blocks[0]
        predecessor: str | None = None

        while True:
            for instruction in block.instructions:
                result = self.eval_instruction(instruction, values, predecessor, depth)
                if instruction.result is not None:
                    values[instruction.result] = result

            terminator = block.terminator
            assert terminator is not None
            if terminator.op == "return":
                return self.resolve(terminator.args[0], values)
            if terminator.op == "jump":
                predecessor, block = block.label, blocks[terminator.args[0]]
                continue
            if terminator.op == "branch":
                condition = self.resolve(terminator.args[0], values)
                target = terminator.args[1] if bool(condition) else terminator.args[2]
                predecessor, block = block.label, blocks[target]
                continue
            raise RuntimeTrap(f"runtime trap: unknown terminator {terminator.op}")

    def resolve(self, name: str, values: dict[str, int | bool]) -> int | bool:
        if name == "true":
            return True
        if name == "false":
            return False
        return values[name]

    def eval_instruction(
        self,
        instruction: Instruction,
        values: dict[str, int | bool],
        predecessor: str | None,
        depth: int,
    ) -> int | bool:
        op = instruction.op
        if op == "const":
            return instruction.attrs["value"]
        if op == "phi":
            for label, value in instruction.attrs["incoming"]:
                if label == predecessor:
                    return self.resolve(value, values)
            raise RuntimeTrap("runtime trap: phi has no value for predecessor")
        if op == "call":
            args = tuple(self.resolve(arg, values) for arg in instruction.args)
            return self.call(instruction.attrs["callee"], args, depth + 1)
        if op == "print.i64":
            value = self.resolve(instruction.args[0], values)
            self.output.append(f"{int(value)}\n")
            return 0
        if op == "bool.not":
            return not bool(self.resolve(instruction.args[0], values))

        left = self.resolve(instruction.args[0], values)
        right = self.resolve(instruction.args[1], values)
        if op == "iadd.checked":
            return checked_i64(int(left) + int(right))
        if op == "isub.checked":
            return checked_i64(int(left) - int(right))
        if op == "imul.checked":
            return checked_i64(int(left) * int(right))
        if op == "idiv.checked":
            return checked_div(int(left), int(right))
        if op == "irem.checked":
            quotient = checked_div(int(left), int(right))
            return int(left) - quotient * int(right)
        if op == "icmp.eq":
            return left == right
        if op == "icmp.ne":
            return left != right
        if op == "icmp.slt":
            return int(left) < int(right)
        if op == "icmp.sle":
            return int(left) <= int(right)
        if op == "icmp.sgt":
            return int(left) > int(right)
        if op == "icmp.sge":
            return int(left) >= int(right)
        raise RuntimeTrap(f"runtime trap: unknown instruction {op}")


def checked_i64(value: int) -> int:
    if value < I64_MIN or value > I64_MAX:
        raise RuntimeTrap("runtime trap: signed 64-bit integer overflow")
    return value


def checked_div(left: int, right: int) -> int:
    if right == 0:
        raise RuntimeTrap("runtime trap: division by zero")
    if left == I64_MIN and right == -1:
        raise RuntimeTrap("runtime trap: signed 64-bit integer overflow")
    return abs(left) // abs(right) * (-1 if (left < 0) != (right < 0) else 1)
