#!/usr/bin/env python3
# stage5_bytecode.py - STAGE 5: compile to bytecode, execute on a VM.
#
# This stage crosses the line from "interpreter" to "compiler".
#
# Stages 2-4 executed the TREE: control flow borrowed Python's if/while,
# and every execution re-walked the AST. Here we translate the tree ONCE
# into a flat list of instructions, then execute that list on a stack
# machine with an explicit program counter:
#
#   source -> lex -> parse -> [ COMPILE: AST -> bytecode ] -> [ VM runs it ]
#
# Two ideas carry all the weight:
#
#   1. Expression trees flatten into stack code by post-order walk:
#        (1 + 2) * x   =>   CONST 1; CONST 2; BINOP +; LOAD x; BINOP *
#      Operands first, operator last. That is the whole trick.
#
#   2. Structured control flow (if/while) lowers to conditional jumps.
#      When we emit a forward jump we do not yet know its target, so we
#      emit a placeholder and PATCH it once the target is known
#      ("backpatching"). Real compilers do exactly this with labels.
#
# CPython, the JVM, and Lua all run on this model. Native codegen
# (compendium: minic.py via LLVM, tinyx86.py directly) is "the same
# lowering, but the instruction list is real machine code".
#
# Usage:
#   python3 stage5_bytecode.py program.mini          run it
#   python3 stage5_bytecode.py --dis program.mini    show the bytecode

import sys
from stage3_functions import lex, Parser

ARITH = {"+", "-", "*", "/", "%"}
COMPARE = {"<", "<=", ">", ">=", "==", "!="}

# --- 1. Compiler: AST -> list of instruction tuples --------------------------
# Instruction set (one frame's operand stack, variables in the frame):
#   ("CONST", v)        push constant
#   ("LOAD", name)      push variable
#   ("STORE", name)     pop into variable
#   ("BINOP", op)       pop rhs, pop lhs, push lhs op rhs
#   ("NEG",)            pop v, push -v
#   ("JMP", target)     pc = target
#   ("JMPF", target)    pop v; if v == 0 then pc = target
#   ("CALL", f, argc)   pop argc args, invoke f, push its return value
#   ("RET",)            pop v, return v to the caller
#   ("PRINT",)          pop v, print it
#   ("POP",)            pop and discard (expression statements)

class Compiler:
    def __init__(self):
        self.code = []

    def emit(self, *ins):
        self.code.append(tuple(ins))
        return len(self.code) - 1          # index, for backpatching

    def here(self):
        return len(self.code)

    def patch(self, at, target):
        op = self.code[at][0]
        self.code[at] = (op, target)

    def compile_func(self, body):
        self.code = []
        for s in body:
            self.compile_stmt(s)
        self.emit("CONST", 0)              # implicit 'return 0'
        self.emit("RET")
        return self.code

    def compile_stmt(self, s):
        kind = s[0]
        if kind in ("let", "assign"):      # identical once names are frame-flat
            self.compile_expr(s[2])
            self.emit("STORE", s[1])
        elif kind == "return":
            self.compile_expr(s[1])
            self.emit("RET")
        elif kind == "print":
            self.compile_expr(s[1])
            self.emit("PRINT")
        elif kind == "exprstmt":
            self.compile_expr(s[1])
            self.emit("POP")
        elif kind == "if":
            #   <cond>; JMPF else; <then>; JMP end; else: <else>; end:
            self.compile_expr(s[1])
            jf = self.emit("JMPF", None)
            for st in s[2]:
                self.compile_stmt(st)
            if s[3] is not None:
                jend = self.emit("JMP", None)
                self.patch(jf, self.here())
                for st in s[3]:
                    self.compile_stmt(st)
                self.patch(jend, self.here())
            else:
                self.patch(jf, self.here())
        elif kind == "while":
            #   top: <cond>; JMPF end; <body>; JMP top; end:
            top = self.here()
            self.compile_expr(s[1])
            jf = self.emit("JMPF", None)
            for st in s[2]:
                self.compile_stmt(st)
            self.emit("JMP", top)
            self.patch(jf, self.here())
        else:
            raise AssertionError(kind)

    def compile_expr(self, node):
        kind = node[0]
        if kind == "num":
            self.emit("CONST", node[1])
        elif kind == "var":
            self.emit("LOAD", node[1])
        elif kind == "neg":
            self.compile_expr(node[1])
            self.emit("NEG")
        elif kind == "call":
            for a in node[2]:              # arguments left to right
                self.compile_expr(a)
            self.emit("CALL", node[1], len(node[2]))
        elif kind in ARITH or kind in COMPARE:
            self.compile_expr(node[1])     # post-order: lhs, rhs, then op
            self.compile_expr(node[2])
            self.emit("BINOP", kind)
        else:
            raise AssertionError(kind)

# --- 2. VM: execute the instruction list --------------------------------------

BINOPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: int(a / b),
    "%": lambda a, b: a - int(a / b) * b,
    "<": lambda a, b: 1 if a < b else 0,
    "<=": lambda a, b: 1 if a <= b else 0,
    ">": lambda a, b: 1 if a > b else 0,
    ">=": lambda a, b: 1 if a >= b else 0,
    "==": lambda a, b: 1 if a == b else 0,
    "!=": lambda a, b: 1 if a != b else 0,
}

class VM:
    def __init__(self, funcs):
        self.funcs = funcs                 # name -> (params, code)

    def call(self, name, args):
        if name not in self.funcs:
            raise RuntimeError(f"undefined function {name!r}")
        params, code = self.funcs[name]
        if len(params) != len(args):
            raise RuntimeError(f"{name!r} expects {len(params)} args")
        vars = dict(zip(params, args))     # the frame's variables
        stack = []                         # the frame's operand stack
        pc = 0                             # the program counter
        while True:
            ins = code[pc]
            pc += 1
            op = ins[0]
            if op == "CONST":
                stack.append(ins[1])
            elif op == "LOAD":
                if ins[1] not in vars:
                    raise RuntimeError(f"undefined variable {ins[1]!r}")
                stack.append(vars[ins[1]])
            elif op == "STORE":
                vars[ins[1]] = stack.pop()
            elif op == "BINOP":
                rhs = stack.pop()
                lhs = stack.pop()
                stack.append(BINOPS[ins[1]](lhs, rhs))
            elif op == "NEG":
                stack.append(-stack.pop())
            elif op == "JMP":
                pc = ins[1]
            elif op == "JMPF":
                if stack.pop() == 0:
                    pc = ins[1]
            elif op == "CALL":
                argc = ins[2]
                callargs = stack[len(stack) - argc:]
                del stack[len(stack) - argc:]
                # Calls recurse into the host here. Making this an explicit
                # frame stack instead is THE exercise: it unlocks tail-call
                # elimination (pop the frame before jumping) - the very
                # property Kofun needs from its backends.
                stack.append(self.call(ins[1], callargs))
            elif op == "RET":
                return stack.pop()
            elif op == "PRINT":
                print(stack.pop())
            elif op == "POP":
                stack.pop()
            else:
                raise AssertionError(op)

# --- 3. Driver ------------------------------------------------------------------

def disassemble(name, params, code):
    print(f"fn {name}({', '.join(params)}):")
    for i, ins in enumerate(code):
        print(f"  {i:3}  " + " ".join(str(x) for x in ins))

def main():
    args = sys.argv[1:]
    show = False
    if args and args[0] == "--dis":
        show = True
        args = args[1:]
    if len(args) != 1:
        print("usage: stage5_bytecode.py [--dis] program.mini", file=sys.stderr)
        sys.exit(1)
    sys.setrecursionlimit(100000)
    src = open(args[0], encoding="utf-8").read()
    ast_funcs = Parser(lex(src)).parse_program()
    compiled = {}
    for name, (params, body) in ast_funcs.items():
        compiled[name] = (params, Compiler().compile_func(body))
    if show:
        for name, (params, code) in compiled.items():
            disassemble(name, params, code)
        return
    if "main" not in compiled:
        raise RuntimeError("no main() function")
    VM(compiled).call("main", [])

if __name__ == "__main__":
    main()
