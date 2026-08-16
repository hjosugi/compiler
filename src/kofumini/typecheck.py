from __future__ import annotations

from dataclasses import dataclass

from . import ast_nodes as ast
from .errors import TypeCheckError


@dataclass(frozen=True, slots=True)
class Signature:
    params: tuple[str, ...]
    result: str


@dataclass(slots=True)
class TypeInfo:
    expression_types: dict[int, str]
    signatures: dict[str, Signature]

    def type_of(self, expr: ast.Expr) -> str:
        return self.expression_types[id(expr)]


def check(program: ast.Program) -> TypeInfo:
    signatures: dict[str, Signature] = {}
    for function in program.functions:
        if function.name in signatures:
            raise TypeCheckError(f"type error: duplicate function {function.name!r}")
        param_names = [param.name for param in function.params]
        if len(param_names) != len(set(param_names)):
            raise TypeCheckError(f"type error in {function.name}: duplicate parameter")
        signatures[function.name] = Signature(
            tuple(param.type_name for param in function.params), function.return_type
        )

    main = signatures.get("main")
    if main is None:
        raise TypeCheckError("type error: program must define fn main() -> Int")
    if main.params or main.result != "Int":
        raise TypeCheckError("type error: main must have signature fn main() -> Int")

    expression_types: dict[int, str] = {}

    def type_expr(expr: ast.Expr, env: dict[str, str], function_name: str) -> str:
        if isinstance(expr, ast.IntLiteral):
            if expr.value > (1 << 63) - 1:
                raise TypeCheckError(
                    f"type error in {function_name}: integer literal is outside signed i64"
                )
            result = "Int"
        elif isinstance(expr, ast.BoolLiteral):
            result = "Bool"
        elif isinstance(expr, ast.VarExpr):
            if expr.name not in env:
                raise TypeCheckError(
                    f"type error in {function_name}: unknown variable {expr.name!r}"
                )
            result = env[expr.name]
        elif isinstance(expr, ast.CallExpr):
            signature = signatures.get(expr.callee)
            if signature is None:
                raise TypeCheckError(
                    f"type error in {function_name}: unknown function {expr.callee!r}"
                )
            actual = tuple(type_expr(arg, env, function_name) for arg in expr.args)
            if actual != signature.params:
                raise TypeCheckError(
                    f"type error in {function_name}: {expr.callee} expects "
                    f"{signature.params}, got {actual}"
                )
            result = signature.result
        elif isinstance(expr, ast.UnaryExpr):
            operand = type_expr(expr.operand, env, function_name)
            expected = "Int" if expr.op == "-" else "Bool"
            if operand != expected:
                raise TypeCheckError(
                    f"type error in {function_name}: unary {expr.op} expects {expected}"
                )
            result = expected
        elif isinstance(expr, ast.BinaryExpr):
            left = type_expr(expr.left, env, function_name)
            right = type_expr(expr.right, env, function_name)
            if expr.op in {"+", "-", "*", "/", "%"}:
                if left != "Int" or right != "Int":
                    raise TypeCheckError(
                        f"type error in {function_name}: {expr.op} expects two Int values"
                    )
                result = "Int"
            elif expr.op in {"<", "<=", ">", ">="}:
                if left != "Int" or right != "Int":
                    raise TypeCheckError(
                        f"type error in {function_name}: {expr.op} expects two Int values"
                    )
                result = "Bool"
            elif expr.op in {"==", "!="}:
                if left != right:
                    raise TypeCheckError(
                        f"type error in {function_name}: equality operands must match"
                    )
                result = "Bool"
            elif expr.op in {"&&", "||"}:
                if left != "Bool" or right != "Bool":
                    raise TypeCheckError(
                        f"type error in {function_name}: {expr.op} expects two Bool values"
                    )
                result = "Bool"
            else:
                raise TypeCheckError(f"type error: unsupported binary operator {expr.op}")
        elif isinstance(expr, ast.IfExpr):
            condition = type_expr(expr.condition, env, function_name)
            then_type = type_expr(expr.then_expr, env, function_name)
            else_type = type_expr(expr.else_expr, env, function_name)
            if condition != "Bool":
                raise TypeCheckError(f"type error in {function_name}: if condition must be Bool")
            if then_type != else_type:
                raise TypeCheckError(
                    f"type error in {function_name}: if branches must have the same type"
                )
            result = then_type
        else:
            raise AssertionError(f"unhandled expression: {type(expr).__name__}")
        expression_types[id(expr)] = result
        return result

    for function in program.functions:
        if not function.body or not isinstance(function.body[-1], ast.ReturnStmt):
            raise TypeCheckError(f"type error in {function.name}: function must end with return")
        env = {param.name: param.type_name for param in function.params}
        returned = False
        for statement in function.body:
            if returned:
                raise TypeCheckError(f"type error in {function.name}: statement after return")
            if isinstance(statement, ast.LetStmt):
                if statement.name in env:
                    raise TypeCheckError(
                        f"type error in {function.name}: duplicate binding {statement.name!r}"
                    )
                actual = type_expr(statement.value, env, function.name)
                if actual != statement.type_name:
                    raise TypeCheckError(
                        f"type error in {function.name}: {statement.name} is declared "
                        f"{statement.type_name}, got {actual}"
                    )
                env[statement.name] = statement.type_name
            elif isinstance(statement, ast.PrintStmt):
                actual = type_expr(statement.value, env, function.name)
                if actual != "Int":
                    raise TypeCheckError(f"type error in {function.name}: print accepts Int only")
            elif isinstance(statement, ast.ReturnStmt):
                actual = type_expr(statement.value, env, function.name)
                if actual != function.return_type:
                    raise TypeCheckError(
                        f"type error in {function.name}: return expects "
                        f"{function.return_type}, got {actual}"
                    )
                returned = True
            else:
                raise AssertionError(f"unhandled statement: {type(statement).__name__}")

    return TypeInfo(expression_types, signatures)
