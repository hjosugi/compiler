# Language From Zero — 言語処理系を 5 段で作る

ゼロから言語を作る段階式チュートリアル。各 stage は単体で動く完全な処理系で、
`diff stageN stageN+1` がそのまま教材になる (chibicc 方式)。
理論解説は GUIDE.md、動作確認済みコマンドは以下。

```sh
python3 stage1_calc.py "1 + 2 * (3 - 1)"            # 5
python3 stage2_interp.py examples/countdown.mini
python3 stage3_functions.py examples/fib.mini        # 0 1 1 2 3 5 ...
python3 stage4_typecheck.py examples/fib.mini        # 検査を通って実行
python3 stage4_typecheck.py examples/bad_int_condition.mini   # type error で拒否
python3 stage5_bytecode.py examples/fib.mini         # VM 実行 (stage3 と同一出力)
python3 stage5_bytecode.py --dis examples/fib.mini   # バイトコードを読む
```

| Stage | 学ぶこと | 追加コード |
|---|---|---|
| 1 電卓 | lexer / BNF / 再帰下降 / 優先順位 / AST / 評価 | stage1_calc.py |
| 2 文と変数 | 文と式 / 環境 / ブロックスコープ / 制御フロー | stage2_interp.py |
| 3 関数 | フレーム / コールスタック / 再帰 / return=例外 | stage3_functions.py |
| 4 静的検査 | 意味解析 / int・bool 型付け規則 / static の意味 | stage4_typecheck.py |
| 5 バイトコード | AST→命令列 / スタックマシン / backpatch / VM | stage5_bytecode.py |
| 6 ネイティブ | compiler-backend-compendium (別 zip) へ接続 | — |

言語は compendium の Mini と同一。stage5 まで登ると、同じ fib.mini が
「木歩き / VM / LLVM 経由ネイティブ / 直接ネイティブ」の 4 形態で動く。

要件: Python 3.10+ のみ (stage6 の接続先で clang が要る)。
