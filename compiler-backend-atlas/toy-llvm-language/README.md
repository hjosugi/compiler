# KofuMini

Python標準libraryだけで動く、typed language→SSA KIR→LLVM IRの教材compilerです。最初は[rootのゼロからtutorial](../docs/00-from-zero.md)を読み、各表示commandで1段ずつ観察してください。

```bash
export PYTHONPATH="$PWD/toy-llvm-language/src"
python3 -m kofumini.cli tokens toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli ast toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli check toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli kir toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli llvm toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli run toy-llvm-language/examples/choose.kofu
```

Sourceの読む順:

1. `tokens.py`, `lexer.py`
2. `ast_nodes.py`, `parser.py`
3. `typecheck.py`
4. `kir.py`, `lower.py`
5. `interpreter.py`
6. `llvm_emitter.py`
7. `compiler.py`, `cli.py`

Examplesには関数、if/phi、短絡評価、型error、overflow trapがあります。`tests/`はfrontendだけでなく、reference結果とLLVM IRの重要構造を検査します。

