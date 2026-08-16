from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any, TypeAlias


TypeName: TypeAlias = str


@dataclass(frozen=True, slots=True)
class Param:
    name: str
    type_name: TypeName


@dataclass(frozen=True, slots=True)
class IntLiteral:
    value: int


@dataclass(frozen=True, slots=True)
class BoolLiteral:
    value: bool


@dataclass(frozen=True, slots=True)
class VarExpr:
    name: str


@dataclass(frozen=True, slots=True)
class CallExpr:
    callee: str
    args: tuple[Expr, ...]


@dataclass(frozen=True, slots=True)
class UnaryExpr:
    op: str
    operand: Expr


@dataclass(frozen=True, slots=True)
class BinaryExpr:
    op: str
    left: Expr
    right: Expr


@dataclass(frozen=True, slots=True)
class IfExpr:
    condition: Expr
    then_expr: Expr
    else_expr: Expr


Expr: TypeAlias = IntLiteral | BoolLiteral | VarExpr | CallExpr | UnaryExpr | BinaryExpr | IfExpr


@dataclass(frozen=True, slots=True)
class LetStmt:
    name: str
    type_name: TypeName
    value: Expr


@dataclass(frozen=True, slots=True)
class PrintStmt:
    value: Expr


@dataclass(frozen=True, slots=True)
class ReturnStmt:
    value: Expr


Stmt: TypeAlias = LetStmt | PrintStmt | ReturnStmt


@dataclass(frozen=True, slots=True)
class Function:
    name: str
    params: tuple[Param, ...]
    return_type: TypeName
    body: tuple[Stmt, ...]


@dataclass(frozen=True, slots=True)
class Program:
    functions: tuple[Function, ...]


def to_dict(node: Any) -> Any:
    if is_dataclass(node):
        raw = {field.name: to_dict(getattr(node, field.name)) for field in fields(node)}
        return {"node": type(node).__name__, **raw}
    if isinstance(node, tuple):
        return [to_dict(item) for item in node]
    if isinstance(node, list):
        return [to_dict(item) for item in node]
    return node
