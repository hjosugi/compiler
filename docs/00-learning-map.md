# 学習マップ

## まず区別する5層

Compilerの話が難しくなる最大の理由は、異なる層をすべて「backend」と呼ぶことです。

| 層 | 主な責任 | 例 |
|---|---|---|
| Frontend | syntax、name resolution、type、ownership | Clang、rustc frontend、KofuMini parser |
| High/Mid IR | 言語意味を保った最適化 | SIL、MLIR dialect、KIR-H、GIMPLE |
| Low IR | targetに近いSSAとmemory model | LLVM IR、Cranelift IR、QBE IL |
| Machine backend | instruction、register、schedule | LLVM CodeGen、GCC RTL backend |
| Toolchain | object、link、runtime、debug、package | MC、LLD、compiler-rt、libc、BOLT |

LLVMはLow IRだけではありません。`llvm-project`はこのうちLow IR以降の大部分と、Clang、LLD、LLDB、runtime、MLIRまで含みます。

初めてcompilerを作る場合は、先に[ゼロから言語とcompilerを作る](00-from-zero.md)を実行しながら読みます。

## 30分で全体を見る

1. `examples/kofumini/choose.kofu`を読む
2. `make kir`でSSA blockを見る
3. `make llvm`でLLVM IRを見る
4. `labs/instruction_selection.py`でIRから命令を選ぶ
5. `labs/linear_scan.py`で無限virtual registerを有限registerへ割り当てる
6. `docs/03-llvm-backend.md`でLLVM本体の対応箇所を読む

## 1週間の学習順

| Day | テーマ | 実習 |
|---:|---|---|
| 1 | Lexer / Parser / Type checker | `tokens`、`ast`、`check` |
| 2 | CFG / SSA / phi | `kir choose.kofu`、dominators lab |
| 3 | scalar optimization | constant folding、DCEを設計する |
| 4 | instruction selection | selector labへ新patternを追加 |
| 5 | liveness / register allocation | intervalを増やしてspillを見る |
| 6 | ABI / object / linker | LLVM IRを`clang -S`と`clang -c`で比較 |
| 7 | validation | interpreterとnativeを同じinputで比較 |

## 理解確認

次の質問に答えられれば、backendの骨格を理解しています。

- なぜSSAでは1つのvalueを1回しか定義しないのか
- `phi`はどのCFG edgeの値を選ぶのか
- alias analysisが弱いとload/store最適化が止まる理由
- instruction legalizationとinstruction selectionの違い
- virtual registerとphysical registerの違い
- spillingがruntimeを遅くする理由
- calling conventionがfrontendだけでもbackendだけでも完結しない理由
- object writerとlinkerが別責務である理由
- `-O3`同士でもcompile time、runtime、sizeを別々に測る必要
- reference interpreterがmiscompile検出に役立つ理由
