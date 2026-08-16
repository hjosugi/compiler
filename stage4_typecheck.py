#!/usr/bin/env python3
# stage4_typecheck.py - STAGE 4: static checking BEFORE running.
#
# Nothing about the language's syntax or runtime changes. What changes is
# WHEN errors are found: stages 2-3 discover an undefined variable only
# if execution happens to reach it; this stage rejects the whole program
# up front. That is the entire meaning of "static".
#
# The checker is deliberately a separate module that slots between the
# parser and the interpreter - so this file just imports stage 3 and adds
# one pass:
#
#   source -> lex -> parse -> [ CHECK ] -> interpret
#
# We give Mini a tiny type system with two types:
#   int  : numbers, arithmetic, function parameters and returns
#   bool : the result of comparisons; the only thing if/while accept
#
# Typing rules (read "e : t" as "e has type t"):
#   n literal              : int
#   e1 + e2   (both int)   : int        (same for - * / % and unary -)
#   e1 < e2   (both int)   : bool       (same for <= > >= == !=)
#   f(a1..an) (all int, f defined with n params) : int
#   let x = e              : x gets e's type, once per scope
#   x = e                  : e's type must equal x's declared type
#   if (c) / while (c)     : c must be bool   <- '1' is NOT a condition here
#   return e / print(e)    : e must be int
#
# Usage: python3 stage4_typecheck.py program.mini

import sys
from stage3_functions import lex, Parser, Interp

INT, BOOL = "int", "bool"
ARITH = {"+", "-", "*", "/", "%"}
COMPARE = {"<", "<=", ">", ">=", "==", "!="}


class TypeError_(Exception):
    pass


class Checker:
    def __init__(self, funcs):
        self.funcs = funcs                 # name -> (params, body)

    # -- scope handling: a stack of dicts (name -> type) ------------------

    def push(self):
        self.scopes.append({})

    def pop(self):
        self.scopes.pop()

    def define(self, name, t):
        if name in self.scopes[-1]:
            raise TypeError_(f"variable {name!r} already declared in this scope")
        self.scopes[-1][name] = t

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise TypeError_(f"undefined variable {name!r}")

    # -- entry points -------------------------------------------------------

    def check_program(self):
        if "main" not in self.funcs:
            raise TypeError_("no main() function")
        for name, (params, body) in self.funcs.items():
            self.check_func(name, params, body)

    def check_func(self, name, params, body):
        self.scopes = [{}]
        for p in params:
            self.define(p, INT)            # all parameters are int by decree
        self.check_block(body, new_scope=False)

    def check_block(self, stmts, new_scope=True):
        if new_scope:
            self.push()
        for s in stmts:
            self.check_stmt(s)
        if new_scope:
            self.pop()

    # -- statements -----------------------------------------------------------

    def check_stmt(self, s):
        kind = s[0]
        if kind == "let":
            self.define(s[1], self.check_expr(s[2]))
        elif kind == "assign":
            declared = self.lookup(s[1])
            actual = self.check_expr(s[2])
            if declared != actual:
                raise TypeError_(
                    f"cannot assign {actual} to {s[1]!r} (declared {declared})")
        elif kind == "return":
            self.require(s[1], INT, "return value")
        elif kind == "print":
            self.require(s[1], INT, "print argument")
        elif kind == "exprstmt":
            self.check_expr(s[1])
        elif kind == "if":
            self.require(s[1], BOOL, "if condition")
            self.check_block(s[2])
            if s[3] is not None:
                self.check_block(s[3])
        elif kind == "while":
            self.require(s[1], BOOL, "while condition")
            self.check_block(s[2])
        else:
            raise AssertionError(kind)

    def require(self, expr, expected, what):
        actual = self.check_expr(expr)
        if actual != expected:
            raise TypeError_(f"{what} must be {expected}, got {actual}")

    # -- expressions ------------------------------------------------------------

    def check_expr(self, node):
        kind = node[0]
        if kind == "num":
            return INT
        if kind == "var":
            return self.lookup(node[1])
        if kind == "neg":
            if self.check_expr(node[1]) != INT:
                raise TypeError_("unary '-' needs an int")
            return INT
        if kind == "call":
            name, args = node[1], node[2]
            if name not in self.funcs:
                raise TypeError_(f"undefined function {name!r}")
            params = self.funcs[name][0]
            if len(params) != len(args):
                raise TypeError_(
                    f"{name!r} expects {len(params)} args, got {len(args)}")
            for a in args:
                if self.check_expr(a) != INT:
                    raise TypeError_(f"arguments of {name!r} must be int")
            return INT
        if kind in ARITH:
            for side in (node[1], node[2]):
                if self.check_expr(side) != INT:
                    raise TypeError_(f"operands of {kind!r} must be int")
            return INT
        if kind in COMPARE:
            for side in (node[1], node[2]):
                if self.check_expr(side) != INT:
                    raise TypeError_(f"operands of {kind!r} must be int")
            return BOOL
        raise AssertionError(kind)


def main():
    if len(sys.argv) != 2:
        print("usage: stage4_typecheck.py program.mini", file=sys.stderr)
        sys.exit(1)
    sys.setrecursionlimit(100000)
    src = open(sys.argv[1], encoding="utf-8").read()
    funcs = Parser(lex(src)).parse_program()
    try:
        Checker(funcs).check_program()     # the only new step
    except TypeError_ as e:
        print(f"type error: {e}", file=sys.stderr)
        sys.exit(1)
    Interp(funcs).call("main", [])


if __name__ == "__main__":
    main()
