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
class Compilation:
    tokens: list[Token]
    ast: Program
    type_info: TypeInfo
    kir: KIRModule
    llvm_ir: str


def compile_source(source: str, source_name: str = "module.kofu") -> Compilation:
    tokens = lex(source)
    program = parse(tokens)
    type_info = check(program)
    kir = lower(program, type_info)
    llvm_ir = emit_llvm(kir, source_name)
    return Compilation(tokens, program, type_info, kir, llvm_ir)
