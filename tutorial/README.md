# Language From Zero — 言語処理系を5段で作る

ゼロから言語を作る段階式tutorialです。各stageは単体で動く処理系で、前後のsource差分から、その段で増えた概念を読めます。詳しい理論は[段階guide](../docs/tutorial-stages.md)を参照してください。

repository rootから実行します。

```bash
python3 tutorial/stage1_calc.py "1 + 2 * (3 - 1)"
python3 tutorial/stage2_interp.py tutorial/examples/countdown.mini
python3 tutorial/stage3_functions.py tutorial/examples/fib.mini
python3 tutorial/stage4_typecheck.py tutorial/examples/fib.mini
python3 tutorial/stage4_typecheck.py tutorial/examples/bad_int_condition.mini
python3 tutorial/stage5_bytecode.py tutorial/examples/fib.mini
python3 tutorial/stage5_bytecode.py --dis tutorial/examples/fib.mini
```

| Stage | 学ぶこと | Source |
|---:|---|---|
| 1 電卓 | lexer、BNF、再帰下降、優先順位、AST、評価 | [`stage1_calc.py`](stage1_calc.py) |
| 2 文と変数 | 文と式、環境chain、block scope、制御flow | [`stage2_interp.py`](stage2_interp.py) |
| 3 関数 | frame、call stack、再帰、`return`による脱出 | [`stage3_functions.py`](stage3_functions.py) |
| 4 静的検査 | 意味解析、`int`/`bool`、実行前error | [`stage4_typecheck.py`](stage4_typecheck.py) |
| 5 bytecode | AST→命令列、lexical slot、jump、backpatch、VM | [`stage5_bytecode.py`](stage5_bytecode.py) |
| 次の一周 | typed SSA KIR→LLVM IR→native | [KofuMini](../docs/00-from-zero.md) |

境界例も実行できます。

```bash
python3 tutorial/stage5_bytecode.py tutorial/examples/block_shadowing.mini
python3 tutorial/stage5_bytecode.py tutorial/examples/zero_arg_call.mini
```

このMini dialectは、stage間diffを小さくするため型注釈のない文中心の言語です。KofuMiniはtyped SSAとLLVM loweringを学ぶ別dialectです。概念は連続していますが、syntaxとASTは同一ではありません。

要件はPython 3.11以上です。全stageの回帰testはrepository rootで`make check-python`を実行してください。
