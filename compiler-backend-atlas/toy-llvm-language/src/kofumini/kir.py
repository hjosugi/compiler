from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import VerificationError


@dataclass(slots=True)
class Instruction:
    op: str
    result: str | None = None
    type_name: str | None = None
    args: tuple[str, ...] = ()
    attrs: dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        target = f"{self.result}:{self.type_name} = " if self.result else ""
        args = ", ".join(self.args)
        if self.op == "const":
            args = str(self.attrs["value"]).lower()
        elif self.op == "call":
            args = f"{self.attrs['callee']}({args})"
        elif self.op == "phi":
            args = ", ".join(
                f"[{value}, {label}]" for label, value in self.attrs["incoming"]
            )
        return f"{target}{self.op} {args}".rstrip()


@dataclass(slots=True)
class Terminator:
    op: str
    args: tuple[str, ...]

    def render(self) -> str:
        return f"{self.op} {', '.join(self.args)}"


@dataclass(slots=True)
class Block:
    label: str
    instructions: list[Instruction] = field(default_factory=list)
    terminator: Terminator | None = None

    def render(self) -> str:
        lines = [f"{self.label}:"]
        lines.extend(f"  {instruction.render()}" for instruction in self.instructions)
        if self.terminator is not None:
            lines.append(f"  {self.terminator.render()}")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class KIRParam:
    name: str
    type_name: str
    value: str


@dataclass(slots=True)
class KIRFunction:
    name: str
    params: tuple[KIRParam, ...]
    return_type: str
    blocks: list[Block]

    def render(self) -> str:
        params = ", ".join(f"{p.value}:{p.type_name}" for p in self.params)
        body = "\n".join(block.render() for block in self.blocks)
        return f"fn {self.name}({params}) -> {self.return_type} {{\n{body}\n}}"


@dataclass(slots=True)
class KIRModule:
    functions: list[KIRFunction]

    def render(self) -> str:
        return "\n\n".join(function.render() for function in self.functions) + "\n"


def verify(module: KIRModule) -> None:
    function_names: set[str] = set()
    for function in module.functions:
        if function.name in function_names:
            raise VerificationError(f"KIR verifier: duplicate function {function.name}")
        function_names.add(function.name)
        if not function.blocks:
            raise VerificationError(f"KIR verifier: {function.name} has no blocks")

        labels = [block.label for block in function.blocks]
        label_set = set(labels)
        if len(labels) != len(label_set):
            raise VerificationError(f"KIR verifier: duplicate block in {function.name}")

        definitions = {param.value for param in function.params}
        for block in function.blocks:
            if block.terminator is None:
                raise VerificationError(
                    f"KIR verifier: unterminated block {function.name}:{block.label}"
                )
            for instruction in block.instructions:
                if instruction.result:
                    if instruction.result in definitions:
                        raise VerificationError(
                            f"KIR verifier: duplicate SSA value {instruction.result}"
                        )
                    definitions.add(instruction.result)
                if instruction.op == "phi":
                    incoming_labels = {label for label, _ in instruction.attrs["incoming"]}
                    if not incoming_labels <= label_set:
                        raise VerificationError(
                            f"KIR verifier: phi in {block.label} references unknown block"
                        )

            terminator = block.terminator
            if terminator.op == "jump":
                if terminator.args[0] not in label_set:
                    raise VerificationError(
                        f"KIR verifier: jump to unknown block {terminator.args[0]}"
                    )
            elif terminator.op == "branch":
                if len(terminator.args) != 3:
                    raise VerificationError("KIR verifier: branch needs condition and targets")
                if terminator.args[1] not in label_set or terminator.args[2] not in label_set:
                    raise VerificationError("KIR verifier: branch references unknown block")
            elif terminator.op != "return":
                raise VerificationError(
                    f"KIR verifier: unknown terminator {terminator.op}"
                )

