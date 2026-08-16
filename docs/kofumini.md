# KofuMini

Python標準libraryだけで動く、typed language→SSA KIR→LLVM IRの教材compilerです。最初は[ゼロからのwalkthrough](00-from-zero.md)を読み、各表示commandで1段ずつ観察してください。

```bash
export PYTHONPATH="$PWD/src"
python3 -m kofumini.cli tokens examples/kofumini/choose.kofu
python3 -m kofumini.cli ast examples/kofumini/choose.kofu
python3 -m kofumini.cli check examples/kofumini/choose.kofu
python3 -m kofumini.cli kir examples/kofumini/choose.kofu
python3 -m kofumini.cli kir-json examples/kofumini/choose.kofu
python3 -m kofumini.cli kir-hash examples/kofumini/choose.kofu
python3 -m kofumini.cli llvm examples/kofumini/choose.kofu
python3 -m kofumini.cli run examples/kofumini/choose.kofu
```

各commandは観察対象のphaseまでだけ実行します。`tokens`はlexer、`ast`はparser、`check`はtype checkerで停止し、`kir`/`run`はloweringまで、`llvm`/`build`はLLVM emitterまで進みます。前段の表示に後段の制約を誤って混ぜません。

Sourceの読む順:

1. `src/kofumini/tokens.py`, `lexer.py`
2. `src/kofumini/ast_nodes.py`, `parser.py`
3. `src/kofumini/typecheck.py`
4. `src/kofumini/kir.py`, `lower.py`
5. `src/kofumini/interpreter.py`
6. `src/kofumini/llvm_emitter.py`
7. `src/kofumini/compiler.py`, `cli.py`

Examplesには関数、if/phi、短絡評価、型error、signed i64境界、overflow trapがあります。IdentifierはKofuMini v1ではASCIIです。`tests/`はfrontend、phase-aware CLI、canonical KIR/hash、strict SSA verifier、reference結果、LLVM IR/native経路を検査します。
