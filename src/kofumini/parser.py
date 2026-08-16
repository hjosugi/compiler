from __future__ import annotations

from .ast_nodes import (
    BinaryExpr,
    BoolLiteral,
    CallExpr,
    Function,
    IfExpr,
    IntLiteral,
    LetStmt,
    Param,
    PrintStmt,
    Program,
    ReturnStmt,
    UnaryExpr,
    VarExpr,
)
from .errors import ParseError
from .tokens import Token

PRECEDENCE = {
    "OROR": 1,
    "ANDAND": 2,
    "EQEQ": 3,
    "NE": 3,
    "LT": 4,
    "LE": 4,
    "GT": 4,
    "GE": 4,
    "PLUS": 5,
    "MINUS": 5,
    "STAR": 6,
    "SLASH": 6,
    "PERCENT": 6,
}

OP_TEXT = {
    "OROR": "||",
    "ANDAND": "&&",
    "EQEQ": "==",
    "NE": "!=",
    "LT": "<",
    "LE": "<=",
    "GT": ">",
    "GE": ">=",
    "PLUS": "+",
    "MINUS": "-",
    "STAR": "*",
    "SLASH": "/",
    "PERCENT": "%",
}


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def at(self, kind: str) -> bool:
        return self.current().kind == kind

    def consume(self, kind: str) -> Token:
        token = self.current()
        if token.kind != kind:
            raise ParseError(
                f"parse error at {token.location()}: expected {kind}, got {token.kind}"
            )
        self.index += 1
        return token

    def parse_program(self) -> Program:
        functions: list[Function] = []
        while not self.at("EOF"):
            functions.append(self.parse_function())
        if not functions:
            raise ParseError("parse error: program must contain at least one function")
        return Program(tuple(functions))

    def parse_function(self) -> Function:
        self.consume("FN")
        name = self.consume("IDENT").text
        self.consume("LPAREN")
        params: list[Param] = []
        if not self.at("RPAREN"):
            while True:
                param_name = self.consume("IDENT").text
                self.consume("COLON")
                params.append(Param(param_name, self.parse_type()))
                if not self.at("COMMA"):
                    break
                self.consume("COMMA")
        self.consume("RPAREN")
        self.consume("ARROW")
        return_type = self.parse_type()
        self.consume("LBRACE")
        body = []
        while not self.at("RBRACE"):
            body.append(self.parse_statement())
        self.consume("RBRACE")
        return Function(name, tuple(params), return_type, tuple(body))

    def parse_type(self) -> str:
        if self.at("INT_TYPE"):
            return self.consume("INT_TYPE").text
        if self.at("BOOL_TYPE"):
            return self.consume("BOOL_TYPE").text
        token = self.current()
        raise ParseError(f"parse error at {token.location()}: expected a type")

    def parse_statement(self):
        if self.at("LET"):
            self.consume("LET")
            name = self.consume("IDENT").text
            self.consume("COLON")
            type_name = self.parse_type()
            self.consume("EQ")
            value = self.parse_expression()
            self.consume("SEMI")
            return LetStmt(name, type_name, value)
        if self.at("PRINT"):
            self.consume("PRINT")
            self.consume("LPAREN")
            value = self.parse_expression()
            self.consume("RPAREN")
            self.consume("SEMI")
            return PrintStmt(value)
        if self.at("RETURN"):
            self.consume("RETURN")
            value = self.parse_expression()
            self.consume("SEMI")
            return ReturnStmt(value)
        token = self.current()
        raise ParseError(f"parse error at {token.location()}: expected a statement")

    def parse_expression(self, min_precedence: int = 0):
        left = self.parse_prefix()
        while True:
            token = self.current()
            precedence = PRECEDENCE.get(token.kind)
            if precedence is None or precedence < min_precedence:
                break
            self.index += 1
            right = self.parse_expression(precedence + 1)
            left = BinaryExpr(OP_TEXT[token.kind], left, right)
        return left

    def parse_prefix(self):
        token = self.current()
        if token.kind == "INT":
            self.index += 1
            return IntLiteral(int(token.text))
        if token.kind == "TRUE":
            self.index += 1
            return BoolLiteral(True)
        if token.kind == "FALSE":
            self.index += 1
            return BoolLiteral(False)
        if token.kind == "IDENT":
            self.index += 1
            if self.at("LPAREN"):
                self.consume("LPAREN")
                args = []
                if not self.at("RPAREN"):
                    while True:
                        args.append(self.parse_expression())
                        if not self.at("COMMA"):
                            break
                        self.consume("COMMA")
                self.consume("RPAREN")
                return CallExpr(token.text, tuple(args))
            return VarExpr(token.text)
        if token.kind in {"MINUS", "BANG"}:
            self.index += 1
            op = "-" if token.kind == "MINUS" else "!"
            return UnaryExpr(op, self.parse_expression(7))
        if token.kind == "LPAREN":
            self.consume("LPAREN")
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr
        if token.kind == "IF":
            return self.parse_if_expression()
        raise ParseError(f"parse error at {token.location()}: expected an expression")

    def parse_if_expression(self) -> IfExpr:
        self.consume("IF")
        condition = self.parse_expression()
        self.consume("LBRACE")
        then_expr = self.parse_expression()
        self.consume("RBRACE")
        self.consume("ELSE")
        self.consume("LBRACE")
        else_expr = self.parse_expression()
        self.consume("RBRACE")
        return IfExpr(condition, then_expr, else_expr)


def parse(tokens: list[Token]) -> Program:
    return Parser(tokens).parse_program()
