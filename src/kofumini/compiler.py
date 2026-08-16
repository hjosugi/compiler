from __future__ import annotations

from dataclasses import dataclass

from .ast_nodes import Program
from .kir import KIRModule
from .lexer import lex
from .llvm_emitter import emit_llvm
from .lower import lower
from .parser import parse
from .tokens import Token
from .typecheck import TypeInfo, check


@dataclass(slots=True)
class ParsedSource:
    tokens: list[Token]
    ast: Program


@dataclass(slots=True)
class CheckedSource(ParsedSource):
    type_info: TypeInfo


@dataclass(slots=True)
class LoweredSource(CheckedSource):
    kir: KIRModule


@dataclass(slots=True)
class Compilation(LoweredSource):
    llvm_ir: str


def tokenize_source(source: str) -> list[Token]:
    return lex(source)


def parse_source(source: str) -> ParsedSource:
    tokens = tokenize_source(source)
    return ParsedSource(tokens, parse(tokens))


def check_source(source: str) -> CheckedSource:
    parsed = parse_source(source)
    return CheckedSource(parsed.tokens, parsed.ast, check(parsed.ast))


def lower_source(source: str) -> LoweredSource:
    checked = check_source(source)
    kir = lower(checked.ast, checked.type_info)
    return LoweredSource(checked.tokens, checked.ast, checked.type_info, kir)


def compile_source(source: str, source_name: str = "module.kofu") -> Compilation:
    lowered = lower_source(source)
    llvm_ir = emit_llvm(lowered.kir, source_name)
    return Compilation(
        lowered.tokens,
        lowered.ast,
        lowered.type_info,
        lowered.kir,
        llvm_ir,
    )
