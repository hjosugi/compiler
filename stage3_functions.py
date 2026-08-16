#!/usr/bin/env python3
# stage3_functions.py - STAGE 3: functions, calls, recursion.
#
# New concepts over stage 2 (diff the files!):
#   * a program is now a list of function definitions; execution starts
#     at main()
#   * a CALL creates a fresh environment for the callee's parameters:
#     that environment IS the "stack frame". The call stack is Python's
#     own recursion here - stage 5 makes it an explicit data structure.
#   * 'return' must abandon whatever statements remain, however deeply
#     nested. Implemented as an exception - the standard trick in
#     tree-walking interpreters (Crafting Interpreters does the same).
#
# This completes the Mini language from the compendium's minilang/:
# the same fib.mini runs here (interpreted) and under minic.py (compiled
# via LLVM). Same AST shape, two different back halves.
#
# Usage: python3 stage3_functions.py program.mini

import sys

KEYWORDS = {"fn", "let", "if", "else", "while", "return", "print"}
TWO_CHAR = {"==", "!=", "<=", ">="}

# --- 1. Lexer (unchanged apart from two new keywords) ----------------------

def lex(src):
    toks, i, line = [], 0, 1
    while i < len(src):
        c = src[i]
        if c == "\n":
            line += 1; i += 1
        elif c.isspace():
            i += 1
        elif c == "#":
            while i < len(src) and src[i] != "\n":
                i += 1
        elif c.isdigit():
            j = i
            while j < len(src) and src[j].isdigit():
                j += 1
            toks.append(("num", int(src[i:j]), line)); i = j
        elif c.isalpha() or c == "_":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            w = src[i:j]
            toks.append((w if w in KEYWORDS else "ident", w, line)); i = j
        elif src[i:i+2] in TWO_CHAR:
            toks.append((src[i:i+2], src[i:i+2], line)); i += 2
        elif c in "+-*/%<>=(){};,":
            toks.append((c, c, line)); i += 1
        else:
            raise SyntaxError(f"line {line}: unexpected {c!r}")
    toks.append(("eof", None, line))
    return toks

# --- 2. Parser ---------------------------------------------------------------

class Parser:
    def __init__(self, toks):
        self.toks, self.i = toks, 0
    def peek(self): return self.toks[self.i][0]
    def peek2(self): return self.toks[self.i + 1][0]
    def next(self):
        t = self.toks[self.i]; self.i += 1; return t
    def expect(self, kind):
        t = self.next()
        if t[0] != kind:
            raise SyntaxError(f"line {t[2]}: expected {kind!r}, got {t[1]!r}")
        return t

    def parse_program(self):
        funcs = {}
        while self.peek() != "eof":
            name, params, body = self.parse_func()
            if name in funcs:
                raise SyntaxError(f"function {name!r} defined twice")
            funcs[name] = (params, body)
        return funcs

    def parse_func(self):
        self.expect("fn")
        name = self.expect("ident")[1]
        self.expect("(")
        params = []
        if self.peek() != ")":
            params.append(self.expect("ident")[1])
            while self.peek() == ",":
                self.next()
                params.append(self.expect("ident")[1])
        self.expect(")")
        return name, params, self.parse_block()

    def parse_block(self):
        self.expect("{")
        stmts = []
        while self.peek() != "}":
            stmts.append(self.parse_stmt())
        self.expect("}")
        return stmts

    def parse_stmt(self):
        k = self.peek()
        if k == "let":
            self.next()
            name = self.expect("ident")[1]
            self.expect("=")
            e = self.parse_expr()
            self.expect(";")
            return ("let", name, e)
        if k == "return":
            self.next()
            e = self.parse_expr()
            self.expect(";")
            return ("return", e)
        if k == "print":
            self.next(); self.expect("(")
            e = self.parse_expr()
            self.expect(")"); self.expect(";")
            return ("print", e)
        if k == "if":
            self.next(); self.expect("(")
            cond = self.parse_expr()
            self.expect(")")
            then = self.parse_block()
            els = None
            if self.peek() == "else":
                self.next()
                els = self.parse_block()
            return ("if", cond, then, els)
        if k == "while":
            self.next(); self.expect("(")
            cond = self.parse_expr()
            self.expect(")")
            return ("while", cond, self.parse_block())
        if k == "ident" and self.peek2() == "=":
            name = self.next()[1]
            self.next()
            e = self.parse_expr()
            self.expect(";")
            return ("assign", name, e)
        e = self.parse_expr()          # expression statement, e.g. f(x);
        self.expect(";")
        return ("exprstmt", e)

    def parse_expr(self):
        node = self.parse_add()
        if self.peek() in ("<", "<=", ">", ">=", "==", "!="):
            op = self.next()[0]
            node = (op, node, self.parse_add())
        return node

    def parse_add(self):
        node = self.parse_mul()
        while self.peek() in ("+", "-"):
            op = self.next()[0]
            node = (op, node, self.parse_mul())
        return node

    def parse_mul(self):
        node = self.parse_unary()
        while self.peek() in ("*", "/", "%"):
            op = self.next()[0]
            node = (op, node, self.parse_unary())
        return node

    def parse_unary(self):
        if self.peek() == "-":
            self.next()
            return ("neg", self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        t = self.next()
        if t[0] == "num":
            return ("num", t[1])
        if t[0] == "ident":
            if self.peek() == "(":         # function call
                self.next()
                args = []
                if self.peek() != ")":
                    args.append(self.parse_expr())
                    while self.peek() == ",":
                        self.next()
                        args.append(self.parse_expr())
                self.expect(")")
                return ("call", t[1], args)
            return ("var", t[1])
        if t[0] == "(":
            e = self.parse_expr()
            self.expect(")")
            return e
        raise SyntaxError(f"line {t[2]}: unexpected {t[1]!r}")

# --- 3. Environment (same as stage 2) ----------------------------------------

class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent
    def define(self, name, value):
        if name in self.vars:
            raise RuntimeError(f"variable {name!r} already declared in this scope")
        self.vars[name] = value
    def get(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise RuntimeError(f"undefined variable {name!r}")
    def set(self, name, value):
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        raise RuntimeError(f"undefined variable {name!r}")

# --- 4. Interpreter -----------------------------------------------------------

class ReturnSignal(Exception):
    # Carries the return value up through arbitrarily deep statement
    # nesting. Exceptions are the host-language feature whose dynamic
    # extent matches 'return' exactly - that is why every tree-walker
    # uses them.
    def __init__(self, value):
        self.value = value

class Interp:
    def __init__(self, funcs):
        self.funcs = funcs

    def call(self, name, args):
        if name not in self.funcs:
            raise RuntimeError(f"undefined function {name!r}")
        params, body = self.funcs[name]
        if len(params) != len(args):
            raise RuntimeError(f"{name!r} expects {len(params)} args, got {len(args)}")
        frame = Env()                      # the callee's stack frame
        for p, a in zip(params, args):
            frame.define(p, a)
        try:
            self.exec_block(body, frame, new_scope=False)
        except ReturnSignal as r:
            return r.value
        return 0                           # implicit 'return 0'

    def exec_block(self, stmts, env, new_scope=True):
        inner = Env(env) if new_scope else env
        for s in stmts:
            self.exec_stmt(s, inner)

    def exec_stmt(self, s, env):
        kind = s[0]
        if kind == "let":
            env.define(s[1], self.evaluate(s[2], env))
        elif kind == "assign":
            env.set(s[1], self.evaluate(s[2], env))
        elif kind == "return":
            raise ReturnSignal(self.evaluate(s[1], env))
        elif kind == "print":
            print(self.evaluate(s[1], env))
        elif kind == "exprstmt":
            self.evaluate(s[1], env)
        elif kind == "if":
            if self.evaluate(s[1], env) != 0:
                self.exec_block(s[2], env)
            elif s[3] is not None:
                self.exec_block(s[3], env)
        elif kind == "while":
            while self.evaluate(s[1], env) != 0:
                self.exec_block(s[2], env)
        else:
            raise AssertionError(kind)

    CMP = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
           ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
           "==": lambda a, b: a == b, "!=": lambda a, b: a != b}

    def evaluate(self, node, env):
        kind = node[0]
        if kind == "num":
            return node[1]
        if kind == "var":
            return env.get(node[1])
        if kind == "neg":
            return -self.evaluate(node[1], env)
        if kind == "call":
            args = [self.evaluate(a, env) for a in node[2]]
            return self.call(node[1], args)
        lhs = self.evaluate(node[1], env)
        rhs = self.evaluate(node[2], env)
        if kind == "+": return lhs + rhs
        if kind == "-": return lhs - rhs
        if kind == "*": return lhs * rhs
        if kind == "/": return int(lhs / rhs)
        if kind == "%": return lhs - int(lhs / rhs) * rhs
        if kind in self.CMP:
            return 1 if self.CMP[kind](lhs, rhs) else 0
        raise AssertionError(kind)

def main():
    if len(sys.argv) != 2:
        print("usage: stage3_functions.py program.mini", file=sys.stderr)
        sys.exit(1)
    sys.setrecursionlimit(100000)          # deep Mini recursion = deep Python recursion
    src = open(sys.argv[1], encoding="utf-8").read()
    funcs = Parser(lex(src)).parse_program()
    if "main" not in funcs:
        raise RuntimeError("no main() function")
    Interp(funcs).call("main", [])

if __name__ == "__main__":
    main()
