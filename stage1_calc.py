#!/usr/bin/env python3
# stage1_calc.py - STAGE 1: a calculator.
#
# The smallest complete language pipeline:
#
#   text --(lexer)--> tokens --(parser)--> AST --(evaluator)--> value
#
# Everything later (variables, functions, types, bytecode, native code)
# is grown on top of exactly this skeleton. Read this file top to bottom;
# it is the shape of every compiler you will ever write.
#
# Usage:
#   python3 stage1_calc.py "1 + 2 * (3 - 1)"      -> 5
#
# Grammar (each level = one binding strength; lower = binds tighter):
#   expr    := term  (('+' | '-') term)*        weakest
#   term    := unary (('*' | '/' | '%') unary)*
#   unary   := '-' unary | primary
#   primary := NUMBER | '(' expr ')'             strongest
#
# WHY this layering gives precedence: parse_expr calls parse_term for its
# operands, so by the time '+' combines anything, all '*' inside the
# operands is already grouped. Precedence is not coded anywhere as a
# number - it IS the call graph.

import sys

# --- 1. Lexer: characters -> tokens -------------------------------------

def lex(src):
    toks = []
    i = 0
    while i < len(src):
        c = src[i]
        if c.isspace():
            i += 1
        elif c.isdigit():
            j = i
            while j < len(src) and src[j].isdigit():
                j += 1
            toks.append(("num", int(src[i:j])))
            i = j
        elif c in "+-*/%()":
            toks.append((c, c))
            i += 1
        else:
            raise SyntaxError(f"unexpected character {c!r}")
    toks.append(("eof", None))
    return toks

# --- 2. Parser: tokens -> AST --------------------------------------------
# The AST is plain tuples:
#   ("num", 42)
#   ("neg", expr)
#   ("+", lhs, rhs)   and same for - * / %

class Parser:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def peek(self):
        return self.toks[self.i][0]

    def next(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect(self, kind):
        t = self.next()
        if t[0] != kind:
            raise SyntaxError(f"expected {kind!r}, got {t[1]!r}")
        return t

    def parse_expr(self):
        node = self.parse_term()
        # The while loop makes '+' LEFT-associative:
        # 1-2-3 becomes (1-2)-3, not 1-(2-3).
        while self.peek() in ("+", "-"):
            op = self.next()[0]
            node = (op, node, self.parse_term())
        return node

    def parse_term(self):
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
        if t[0] == "(":
            node = self.parse_expr()
            self.expect(")")
            return node
        raise SyntaxError(f"unexpected token {t[1]!r}")

# --- 3. Evaluator: AST -> value -------------------------------------------
# A "tree-walking interpreter": one Python function per AST node kind,
# recursing into children. This IS the semantics of the language -
# whatever eval does is what the language means.

def evaluate(node):
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "neg":
        return -evaluate(node[1])
    lhs = evaluate(node[1])
    rhs = evaluate(node[2])
    if kind == "+":
        return lhs + rhs
    if kind == "-":
        return lhs - rhs
    if kind == "*":
        return lhs * rhs
    if kind == "/":
        return int(lhs / rhs)   # truncate toward zero, like C
    if kind == "%":
        return lhs - int(lhs / rhs) * rhs
    raise AssertionError(kind)

# --- 4. Driver -------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print('usage: stage1_calc.py "1 + 2 * 3"', file=sys.stderr)
        sys.exit(1)
    ast = Parser(lex(sys.argv[1])).parse_expr()
    print(evaluate(ast))

if __name__ == "__main__":
    main()
