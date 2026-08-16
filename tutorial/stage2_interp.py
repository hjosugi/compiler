#!/usr/bin/env python3
# stage2_interp.py - STAGE 2: variables, statements, control flow.
#
# New concepts over stage 1 (diff the two files!):
#   * statements vs expressions (statements DO, expressions ARE)
#   * an ENVIRONMENT: the mapping from variable names to values
#   * block scope: '{' opens a child environment, '}' throws it away
#   * control flow implemented with the host language's control flow
#     (our 'while' runs on Python's 'while' - stage 5 removes this crutch)
#
# Language (the statement-oriented tutorial Mini dialect):
#   let x = e;   x = e;   print(e);
#   if (e) { ... } else { ... }     while (e) { ... }
#   expressions: + - * / %  comparisons < <= > >= == !=  unary -  ( )
#   condition: 0 is false, non-zero is true.  '#' starts a comment.
#
# Usage: python3 stage2_interp.py program.mini

import sys

KEYWORDS = {"let", "if", "else", "while", "print"}
TWO_CHAR = {"==", "!=", "<=", ">="}

# --- 1. Lexer (now with identifiers, keywords, comments, line numbers) ----

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
        elif c in "+-*/%<>=(){};":
            toks.append((c, c, line)); i += 1
        else:
            raise SyntaxError(f"line {line}: unexpected {c!r}")
    toks.append(("eof", None, line))
    return toks

# --- 2. Parser ---------------------------------------------------------------
# AST statements: ("let", name, e) ("assign", name, e) ("print", e)
#                 ("if", cond, then_block, else_block_or_None)
#                 ("while", cond, block)          block = list of statements
# AST expressions: as stage 1, plus ("var", name) and comparisons.

class Parser:
    def __init__(self, toks):
        self.toks, self.i = toks, 0
    def peek(self): return self.toks[self.i][0]
    def next(self):
        t = self.toks[self.i]; self.i += 1; return t
    def expect(self, kind):
        t = self.next()
        if t[0] != kind:
            raise SyntaxError(f"line {t[2]}: expected {kind!r}, got {t[1]!r}")
        return t

    def parse_program(self):
        stmts = []
        while self.peek() != "eof":
            stmts.append(self.parse_stmt())
        return stmts

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
        # assignment
        name = self.expect("ident")[1]
        self.expect("=")
        e = self.parse_expr()
        self.expect(";")
        return ("assign", name, e)

    # expression grammar: one more level (comparison) above stage 1
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
            return ("var", t[1])
        if t[0] == "(":
            e = self.parse_expr()
            self.expect(")")
            return e
        raise SyntaxError(f"line {t[2]}: unexpected {t[1]!r}")

# --- 3. Environment: where variables live -----------------------------------
# A chain of dicts. Lookup walks outward; 'let' defines in the CURRENT
# scope; assignment updates wherever the name was defined. Entering a
# block pushes a child Env, leaving it just drops the reference.
# (Closures in stage 3+ are exactly "a function holding one of these.")

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

def exec_block(stmts, env):
    inner = Env(env)              # a block gets its own scope
    for s in stmts:
        exec_stmt(s, inner)

def exec_stmt(s, env):
    kind = s[0]
    if kind == "let":
        env.define(s[1], evaluate(s[2], env))
    elif kind == "assign":
        env.set(s[1], evaluate(s[2], env))
    elif kind == "print":
        print(evaluate(s[1], env))
    elif kind == "if":
        if evaluate(s[1], env) != 0:
            exec_block(s[2], env)
        elif s[3] is not None:
            exec_block(s[3], env)
    elif kind == "while":
        while evaluate(s[1], env) != 0:   # host-language while, for now
            exec_block(s[2], env)
    else:
        raise AssertionError(kind)

CMP = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
       ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
       "==": lambda a, b: a == b, "!=": lambda a, b: a != b}

def trunc_div(lhs, rhs):
    if rhs == 0:
        raise ZeroDivisionError("division by zero")
    quotient = abs(lhs) // abs(rhs)
    return -quotient if (lhs < 0) != (rhs < 0) else quotient

def evaluate(node, env):
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "var":
        return env.get(node[1])
    if kind == "neg":
        return -evaluate(node[1], env)
    lhs = evaluate(node[1], env)
    rhs = evaluate(node[2], env)
    if kind == "+": return lhs + rhs
    if kind == "-": return lhs - rhs
    if kind == "*": return lhs * rhs
    if kind == "/": return trunc_div(lhs, rhs)
    if kind == "%": return lhs - trunc_div(lhs, rhs) * rhs
    if kind in CMP:
        return 1 if CMP[kind](lhs, rhs) else 0
    raise AssertionError(kind)

def main():
    if len(sys.argv) != 2:
        print("usage: stage2_interp.py program.mini", file=sys.stderr)
        sys.exit(1)
    src = open(sys.argv[1], encoding="utf-8").read()
    stmts = Parser(lex(src)).parse_program()
    exec_block(stmts, Env())

if __name__ == "__main__":
    main()
