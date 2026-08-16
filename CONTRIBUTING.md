# Contributing

このrepositoryは、説明と実装が同じ意味論を示すことを最優先にします。

変更時は次を確認してください。

1. 正常例、境界例、失敗例のtestを追加する。
2. source semantics、IR invariant、backend前提を混同しない。
3. 時点依存の数値・version・repository一覧にはsnapshot日と一次資料を付ける。
4. benchmarkはhardware、toolchain version、flags、raw outcomeを保存する。
5. `make check`を実行し、LLVM必須の変更では`make check-llvm`も通す。

新しいbackendを追加するときは、KIR reference interpreterとのdifferential testを先に用意してください。性能結果が不一致なら、そのsampleをperformance集計へ含めません。
