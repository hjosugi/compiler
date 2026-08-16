from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, NoReturn

from .errors import VerificationError
from .semantics import I64_MAX, I64_MIN


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
            args = ", ".join(f"[{value}, {label}]" for label, value in self.attrs["incoming"])
        return f"{target}{self.op} {args}".rstrip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "op": self.op,
            "result": self.result,
            "type": self.type_name,
            "args": list(self.args),
            "attrs": self.attrs,
        }


@dataclass(slots=True)
class Terminator:
    op: str
    args: tuple[str, ...]

    def render(self) -> str:
        return f"{self.op} {', '.join(self.args)}"

    def to_dict(self) -> dict[str, Any]:
        return {"op": self.op, "args": list(self.args)}


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "instructions": [instruction.to_dict() for instruction in self.instructions],
            "terminator": self.terminator.to_dict() if self.terminator else None,
        }


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "params": [
                {"name": param.name, "type": param.type_name, "value": param.value}
                for param in self.params
            ],
            "return_type": self.return_type,
            "blocks": [block.to_dict() for block in self.blocks],
        }

    def content_hash(self) -> str:
        payload = {"schema": "kofumini.kir-function/v1", "function": self.to_dict()}
        return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


@dataclass(slots=True)
class KIRModule:
    functions: list[KIRFunction]

    def render(self) -> str:
        return "\n\n".join(function.render() for function in self.functions) + "\n"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "kofumini.kir/v1",
            "functions": [function.to_dict() for function in self.functions],
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_dict())

    def canonical_json(self) -> str:
        return self.canonical_bytes().decode("utf-8")

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def function_hashes(self) -> dict[str, str]:
        return {function.name: function.content_hash() for function in self.functions}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


TYPES = frozenset({"Int", "Bool"})
_SOURCE_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_IR_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*\Z")
_SSA_VALUE = re.compile(r"%[A-Za-z_][A-Za-z0-9_.]*\Z")
ARITHMETIC_OPS = {
    "iadd.checked",
    "isub.checked",
    "imul.checked",
    "idiv.checked",
    "irem.checked",
}
ORDERED_COMPARE_OPS = {"icmp.slt", "icmp.sle", "icmp.sgt", "icmp.sge"}
EQUALITY_COMPARE_OPS = {"icmp.eq", "icmp.ne"}
KNOWN_OPS = (
    {"const", "call", "phi", "print.i64", "bool.not"}
    | ARITHMETIC_OPS
    | ORDERED_COMPARE_OPS
    | EQUALITY_COMPARE_OPS
)


def verify(module: KIRModule) -> None:
    if not module.functions:
        _fail("module has no functions")
    signatures: dict[str, tuple[tuple[str, ...], str]] = {}
    for function in module.functions:
        _require_name(function.name, _SOURCE_IDENTIFIER, "function name")
        if function.name in signatures:
            _fail(f"duplicate function {function.name}")
        if not isinstance(function.return_type, str) or function.return_type not in TYPES:
            _fail(f"unknown return type {function.return_type} in {function.name}")
        param_types = tuple(param.type_name for param in function.params)
        if any(
            not isinstance(type_name, str) or type_name not in TYPES for type_name in param_types
        ):
            _fail(f"unknown parameter type in {function.name}")
        signatures[function.name] = (param_types, function.return_type)

    for function in module.functions:
        _verify_function(function, signatures)


def _verify_function(
    function: KIRFunction,
    signatures: dict[str, tuple[tuple[str, ...], str]],
) -> None:
    if not function.blocks:
        _fail(f"{function.name} has no blocks")

    labels = [block.label for block in function.blocks]
    for label in labels:
        _require_name(label, _IR_IDENTIFIER, "block label")
    if len(labels) != len(set(labels)):
        _fail(f"duplicate block in {function.name}")
    block_by_label = {block.label: block for block in function.blocks}
    predecessors: dict[str, set[str]] = {label: set() for label in labels}
    successors: dict[str, tuple[str, ...]] = {}

    for block in function.blocks:
        terminator = block.terminator
        if terminator is None:
            _fail(f"unterminated block {function.name}:{block.label}")
        if not isinstance(terminator.op, str):
            _fail(f"terminator in {block.label} has a non-string operation")
        if not isinstance(terminator.args, tuple) or any(
            not isinstance(arg, str) for arg in terminator.args
        ):
            _fail(f"terminator {terminator.op} in {block.label} has malformed arguments")
        targets: tuple[str, ...]
        if terminator.op == "jump":
            if len(terminator.args) != 1:
                _fail("jump needs exactly one target")
            targets = (terminator.args[0],)
        elif terminator.op == "branch":
            if len(terminator.args) != 3:
                _fail("branch needs condition and two targets")
            targets = (terminator.args[1], terminator.args[2])
            if targets[0] == targets[1]:
                _fail(f"branch in {block.label} has duplicate targets")
        elif terminator.op == "return":
            if len(terminator.args) != 1:
                _fail("return needs exactly one value")
            targets = ()
        else:
            _fail(f"unknown terminator {terminator.op}")
        for target in targets:
            if target not in block_by_label:
                _fail(f"{block.label} references unknown block {target}")
            predecessors[target].add(block.label)
        successors[block.label] = targets

    entry = labels[0]
    reachable = {entry}
    worklist = [entry]
    while worklist:
        label = worklist.pop()
        for target in successors[label]:
            if target not in reachable:
                reachable.add(target)
                worklist.append(target)
    if reachable != set(labels):
        unreachable = sorted(set(labels) - reachable)
        _fail(f"unreachable blocks in {function.name}: {unreachable}")

    dominators = {label: set(labels) for label in labels}
    dominators[entry] = {entry}
    changed = True
    while changed:
        changed = False
        for label in labels[1:]:
            pred_sets = [dominators[pred] for pred in predecessors[label]]
            new_value = {label} | set.intersection(*pred_sets)
            if new_value != dominators[label]:
                dominators[label] = new_value
                changed = True

    # value -> (type, defining block or None for parameter, instruction index)
    definitions: dict[str, tuple[str, str | None, int]] = {}
    param_names: set[str] = set()
    for param in function.params:
        _require_name(param.name, _SOURCE_IDENTIFIER, "parameter name")
        if param.name in param_names:
            _fail(f"duplicate parameter name {param.name} in {function.name}")
        param_names.add(param.name)
        _require_name(param.value, _SSA_VALUE, "parameter SSA value")
        if param.value in definitions or param.value in {"true", "false"}:
            _fail(f"duplicate or reserved SSA value {param.value}")
        definitions[param.value] = (param.type_name, None, -1)

    for block in function.blocks:
        saw_non_phi = False
        for index, instruction in enumerate(block.instructions):
            if not isinstance(instruction.op, str):
                _fail(f"instruction in {block.label} has a non-string operation")
            if instruction.op not in KNOWN_OPS:
                _fail(f"unknown instruction {instruction.op}")
            if not isinstance(instruction.args, tuple) or any(
                not isinstance(arg, str) for arg in instruction.args
            ):
                _fail(f"{instruction.op} in {block.label} has malformed operands")
            if not isinstance(instruction.attrs, dict) or any(
                not isinstance(key, str) for key in instruction.attrs
            ):
                _fail(f"{instruction.op} in {block.label} has malformed attributes")
            if instruction.op == "phi":
                if saw_non_phi:
                    _fail(f"phi must precede non-phi instructions in {block.label}")
            else:
                saw_non_phi = True
            needs_result = instruction.op != "print.i64"
            if needs_result and instruction.result is None:
                _fail(f"{instruction.op} must define a result")
            if not needs_result and instruction.result is not None:
                _fail(f"{instruction.op} must not define a result")
            if needs_result and (
                not isinstance(instruction.type_name, str) or instruction.type_name not in TYPES
            ):
                _fail(f"{instruction.op} has invalid result type")
            if instruction.result is not None:
                assert isinstance(instruction.type_name, str)
                _require_name(instruction.result, _SSA_VALUE, "instruction SSA value")
                if instruction.result in definitions or instruction.result in {"true", "false"}:
                    _fail(f"duplicate or reserved SSA value {instruction.result}")
                definitions[instruction.result] = (
                    instruction.type_name,
                    block.label,
                    index,
                )

    def value_type(value: str) -> str:
        if value in {"true", "false"}:
            return "Bool"
        _require_name(value, _SSA_VALUE, "SSA operand")
        definition = definitions.get(value)
        if definition is None:
            _fail(f"use of undefined SSA value {value}")
        return definition[0]

    def check_use(
        value: str,
        expected: str,
        use_block: str,
        use_index: int,
        edge_from: str | None = None,
    ) -> None:
        actual = value_type(value)
        if actual != expected:
            _fail(f"{value} has type {actual}, expected {expected}")
        if value in {"true", "false"}:
            return
        _, definition_block, definition_index = definitions[value]
        if definition_block is None:
            return
        destination = edge_from or use_block
        if definition_block == destination:
            if edge_from is None and definition_index >= use_index:
                _fail(f"use before definition of {value} in {use_block}")
            return
        if definition_block not in dominators[destination]:
            _fail(f"definition of {value} does not dominate its use in {use_block}")

    for block in function.blocks:
        for index, instruction in enumerate(block.instructions):
            _verify_instruction(
                instruction,
                block.label,
                index,
                predecessors,
                signatures,
                check_use,
                value_type,
            )

        terminator = block.terminator
        assert terminator is not None
        use_index = len(block.instructions)
        if terminator.op == "branch":
            check_use(terminator.args[0], "Bool", block.label, use_index)
        elif terminator.op == "return":
            check_use(terminator.args[0], function.return_type, block.label, use_index)


def _verify_instruction(
    instruction: Instruction,
    block_label: str,
    index: int,
    predecessors: dict[str, set[str]],
    signatures: dict[str, tuple[tuple[str, ...], str]],
    check_use: Any,
    value_type: Any,
) -> None:
    op = instruction.op
    if op == "const":
        _expect_attrs(instruction, {"value"})
        if instruction.args:
            _fail("const must not have operands")
        value = instruction.attrs["value"]
        if type(value) is bool:
            expected = "Bool"
        elif type(value) is int:
            expected = "Int"
            if not I64_MIN <= value <= I64_MAX:
                _fail("const Int value is outside signed i64")
        else:
            _fail("const value must be Bool or Int")
        if instruction.type_name != expected:
            _fail("const value and result type disagree")
        return
    if op == "call":
        _expect_attrs(instruction, {"callee", "arg_types"})
        callee = instruction.attrs.get("callee")
        if not isinstance(callee, str) or callee not in signatures:
            _fail(f"call references unknown function {callee}")
        param_types, return_type = signatures[callee]
        if len(instruction.args) != len(param_types):
            _fail(f"call to {callee} has wrong argument count")
        arg_types = instruction.attrs["arg_types"]
        if not isinstance(arg_types, (list, tuple)) or tuple(arg_types) != param_types:
            _fail(f"call to {callee} has inconsistent arg_types metadata")
        if instruction.type_name != return_type:
            _fail(f"call to {callee} has wrong result type")
        for value, expected in zip(instruction.args, param_types, strict=True):
            check_use(value, expected, block_label, index)
        return
    if op == "phi":
        _expect_attrs(instruction, {"incoming"})
        incoming = instruction.attrs.get("incoming")
        if not isinstance(incoming, list) or not incoming:
            _fail(f"phi in {block_label} needs incoming edges")
        if any(not isinstance(item, (list, tuple)) or len(item) != 2 for item in incoming):
            _fail(f"malformed phi in {block_label}")
        if any(not isinstance(item[0], str) or not isinstance(item[1], str) for item in incoming):
            _fail(f"malformed phi in {block_label}")
        incoming_labels = [item[0] for item in incoming]
        if len(incoming_labels) != len(set(incoming_labels)):
            _fail(f"duplicate phi predecessor in {block_label}")
        if set(incoming_labels) != predecessors[block_label]:
            _fail(f"phi predecessor set does not match CFG in {block_label}")
        assert instruction.type_name is not None
        for edge_from, value in incoming:
            check_use(value, instruction.type_name, block_label, index, edge_from)
        return
    if op == "print.i64":
        _expect_attrs(instruction, set())
        if instruction.type_name is not None or len(instruction.args) != 1:
            _fail("print.i64 needs one operand and no result type")
        check_use(instruction.args[0], "Int", block_label, index)
        return
    if op == "bool.not":
        _expect_attrs(instruction, set())
        if instruction.type_name != "Bool" or len(instruction.args) != 1:
            _fail("bool.not must have Bool -> Bool type")
        check_use(instruction.args[0], "Bool", block_label, index)
        return
    if op in ARITHMETIC_OPS:
        _expect_attrs(instruction, set())
        if instruction.type_name != "Int" or len(instruction.args) != 2:
            _fail(f"{op} must have (Int, Int) -> Int type")
        for value in instruction.args:
            check_use(value, "Int", block_label, index)
        return
    if op in ORDERED_COMPARE_OPS | EQUALITY_COMPARE_OPS:
        _expect_attrs(instruction, {"operand_type"})
        if instruction.type_name != "Bool" or len(instruction.args) != 2:
            _fail(f"{op} must have two operands and a Bool result")
        operand_type = instruction.attrs.get("operand_type")
        allowed = {"Int"} if op in ORDERED_COMPARE_OPS else TYPES
        if not isinstance(operand_type, str) or operand_type not in allowed:
            _fail(f"{op} has invalid operand_type")
        for value in instruction.args:
            check_use(value, operand_type, block_label, index)
        return
    _fail(f"unhandled instruction {op}")


def _expect_attrs(instruction: Instruction, expected: set[str]) -> None:
    actual = set(instruction.attrs)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    _fail(f"{instruction.op} attribute schema mismatch: missing={missing}, unknown={unknown}")


def _require_name(value: Any, pattern: re.Pattern[str], description: str) -> None:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        _fail(f"invalid {description}: {value!r}")


def _fail(message: str) -> NoReturn:
    raise VerificationError(f"KIR verifier: {message}")
