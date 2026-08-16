from __future__ import annotations

from . import ast_nodes as ast
from .kir import Block, Instruction, KIRFunction, KIRModule, KIRParam, Terminator, verify
from .typecheck import TypeInfo

ARITHMETIC_OPS = {
    "+": "iadd.checked",
    "-": "isub.checked",
    "*": "imul.checked",
    "/": "idiv.checked",
    "%": "irem.checked",
}

COMPARE_OPS = {
    "==": "icmp.eq",
    "!=": "icmp.ne",
    "<": "icmp.slt",
    "<=": "icmp.sle",
    ">": "icmp.sgt",
    ">=": "icmp.sge",
}


class FunctionLowerer:
    def __init__(self, function: ast.Function, type_info: TypeInfo) -> None:
        self.function = function
        self.type_info = type_info
        self.blocks: list[Block] = []
        self.current = self.new_block("entry")
        self.temp_index = 0
        self.block_index = 0
        self.env = {param.name: f"%arg.{param.name}" for param in function.params}

    def new_temp(self) -> str:
        value = f"%v{self.temp_index}"
        self.temp_index += 1
        return value

    def new_block(self, stem: str) -> Block:
        suffix = len(self.blocks)
        block = Block(f"{stem}.{suffix}")
        self.blocks.append(block)
        return block

    def emit(
        self,
        op: str,
        type_name: str | None = None,
        args: tuple[str, ...] = (),
        attrs: dict | None = None,
        has_result: bool = True,
    ) -> str | None:
        result = self.new_temp() if has_result else None
        self.current.instructions.append(Instruction(op, result, type_name, args, attrs or {}))
        return result

    def terminate(self, op: str, *args: str) -> None:
        if self.current.terminator is not None:
            raise AssertionError(f"block {self.current.label} is already terminated")
        self.current.terminator = Terminator(op, tuple(args))

    def lower(self) -> KIRFunction:
        for statement in self.function.body:
            if isinstance(statement, ast.LetStmt):
                self.env[statement.name] = self.lower_expr(statement.value)
            elif isinstance(statement, ast.PrintStmt):
                value = self.lower_expr(statement.value)
                self.emit("print.i64", args=(value,), has_result=False)
            elif isinstance(statement, ast.ReturnStmt):
                value = self.lower_expr(statement.value)
                self.terminate("return", value)
            else:
                raise AssertionError(type(statement).__name__)

        params = tuple(
            KIRParam(param.name, param.type_name, f"%arg.{param.name}")
            for param in self.function.params
        )
        return KIRFunction(self.function.name, params, self.function.return_type, self.blocks)

    def lower_expr(self, expr: ast.Expr) -> str:
        type_name = self.type_info.type_of(expr)
        if isinstance(expr, ast.IntLiteral):
            result = self.emit("const", "Int", attrs={"value": expr.value})
        elif isinstance(expr, ast.BoolLiteral):
            result = self.emit("const", "Bool", attrs={"value": expr.value})
        elif isinstance(expr, ast.VarExpr):
            return self.env[expr.name]
        elif isinstance(expr, ast.CallExpr):
            args = tuple(self.lower_expr(arg) for arg in expr.args)
            signature = self.type_info.signatures[expr.callee]
            result = self.emit(
                "call",
                type_name,
                args=args,
                attrs={"callee": expr.callee, "arg_types": signature.params},
            )
        elif isinstance(expr, ast.UnaryExpr):
            operand = self.lower_expr(expr.operand)
            if expr.op == "!":
                result = self.emit("bool.not", "Bool", args=(operand,))
            else:
                zero = self.emit("const", "Int", attrs={"value": 0})
                assert zero is not None
                result = self.emit("isub.checked", "Int", args=(zero, operand))
        elif isinstance(expr, ast.BinaryExpr):
            if expr.op in {"&&", "||"}:
                return self.lower_short_circuit(expr)
            left = self.lower_expr(expr.left)
            right = self.lower_expr(expr.right)
            if expr.op in ARITHMETIC_OPS:
                result = self.emit(ARITHMETIC_OPS[expr.op], "Int", args=(left, right))
            elif expr.op in COMPARE_OPS:
                result = self.emit(
                    COMPARE_OPS[expr.op],
                    "Bool",
                    args=(left, right),
                    attrs={"operand_type": self.type_info.type_of(expr.left)},
                )
            else:
                raise AssertionError(expr.op)
        elif isinstance(expr, ast.IfExpr):
            return self.lower_if(expr)
        else:
            raise AssertionError(type(expr).__name__)
        assert result is not None
        return result

    def lower_if(self, expr: ast.IfExpr) -> str:
        condition = self.lower_expr(expr.condition)
        then_block = self.new_block("if.then")
        else_block = self.new_block("if.else")
        merge_block = self.new_block("if.merge")
        branch_block = self.current
        self.current = branch_block
        self.terminate("branch", condition, then_block.label, else_block.label)

        self.current = then_block
        then_value = self.lower_expr(expr.then_expr)
        then_end = self.current.label
        self.terminate("jump", merge_block.label)

        self.current = else_block
        else_value = self.lower_expr(expr.else_expr)
        else_end = self.current.label
        self.terminate("jump", merge_block.label)

        self.current = merge_block
        result = self.emit(
            "phi",
            self.type_info.type_of(expr),
            attrs={"incoming": [(then_end, then_value), (else_end, else_value)]},
        )
        assert result is not None
        return result

    def lower_short_circuit(self, expr: ast.BinaryExpr) -> str:
        left = self.lower_expr(expr.left)
        branch_block = self.current
        rhs_block = self.new_block("logic.rhs")
        merge_block = self.new_block("logic.merge")

        self.current = branch_block
        if expr.op == "&&":
            self.terminate("branch", left, rhs_block.label, merge_block.label)
            short_value = "false"
        else:
            self.terminate("branch", left, merge_block.label, rhs_block.label)
            short_value = "true"

        self.current = rhs_block
        rhs_value = self.lower_expr(expr.right)
        rhs_end = self.current.label
        self.terminate("jump", merge_block.label)

        self.current = merge_block
        result = self.emit(
            "phi",
            "Bool",
            attrs={"incoming": [(branch_block.label, short_value), (rhs_end, rhs_value)]},
        )
        assert result is not None
        return result


def lower(program: ast.Program, type_info: TypeInfo) -> KIRModule:
    module = KIRModule(
        [FunctionLowerer(function, type_info).lower() for function in program.functions]
    )
    verify(module)
    return module
