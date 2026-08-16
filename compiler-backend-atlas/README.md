# Compiler Backend Atlas

Compiler backendを「LLVMを呼ぶ方法」だけでなく、frontend、IR、最適化、instruction selection、register allocation、object生成、link、runtime、検証まで一続きで理解するための教材repositoryです。

調査スナップショットは2026-08-16時点です。中心となるLLVM安定版は22.1.8、23.1.0はRC3として扱っています。最新版を無条件に追うのではなく、`toolchain.lock.json`に調査時点の基準を固定しています。

## このrepositoryでできること

- LLVM Organizationと`llvm-project`全体の役割を把握する
- LLVM、GCC、Cranelift、QBE、MLIR、Binaryen、Graal、CompCertなどを比較する
- SSA、CFG、dominance、pass、alias analysisを学ぶ
- instruction selection、register allocation、schedulingを小さなcodeで試す
- 簡易言語KofuMiniをLLVM IRへcompileする
- 同じKIRをreference interpreterで実行し、backend結果と比較する
- Kofunが限定された軸でLLVMを超えるためのarchitectureとroadmapを検討する

## 最短の学習順

1. [ゼロから言語とcompilerを作る](docs/00-from-zero.md)
2. [全体像](docs/00-learning-map.md)
3. [Compiler pipeline](docs/01-compiler-pipeline.md)
4. [LLVM Organization完全整理](docs/02-llvm-organization.md)
5. [LLVM backend内部](docs/03-llvm-backend.md)
6. [主要backend比較](docs/04-backend-landscape.md)
7. [IR・SSA・最適化](docs/05-ir-ssa-optimization.md)
8. [machine code生成](docs/06-machine-code-generation.md)
9. [ABI・object・link・runtime](docs/07-abi-link-runtime.md)
10. [正しさとperformance検証](docs/08-correctness-and-benchmarking.md)
11. [Kofun backend設計](docs/09-kofun-beyond-llvm.md)
12. [実装roadmap](docs/10-implementation-roadmap.md)
13. [用語集](docs/11-glossary.md)
14. [言語史・compiler系譜・設計atlas](docs/12-language-history-design-atlas.md)
15. [段階演習と完成条件](docs/13-exercises.md)

## KofuMiniを動かす

必要条件はPython 3.11以上です。native buildには別途Clang/LLVMが必要です。

```bash
make check
make demo
```

段階ごとに見る場合:

```bash
export PYTHONPATH="$PWD/toy-llvm-language/src"

python3 -m kofumini.cli tokens toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli ast    toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli check  toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli kir    toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli llvm   toy-llvm-language/examples/choose.kofu
python3 -m kofumini.cli run    toy-llvm-language/examples/choose.kofu
```

Clangがある場合:

```bash
python3 -m kofumini.cli build \
  toy-llvm-language/examples/choose.kofu \
  -O2 -o build/choose
./build/choose
```

KofuMiniのpipelineは次のとおりです。

```text
.kofu source
  -> Lexer
  -> Parser / AST
  -> Type checker
  -> typed SSA KIR
  -> KIR verifier
  -> LLVM IR emitter
  -> clang / LLVM optimizer / native codegen
  -> executable
```

同時に、typed SSA KIRはPython reference interpreterでも実行できます。これにより、将来direct backendを追加したときに、frontendの期待結果とmachine codeの結果をdifferential testできます。

## 学習用labs

```bash
python3 labs/dominators.py
python3 labs/instruction_selection.py
python3 labs/linear_scan.py
```

各labは本番compilerの代用品ではありません。algorithmの中心だけを独立させ、入力と出力を追跡するための最小実装です。

## Repository構成

| Path | 内容 |
|---|---|
| `docs/` | 調査、architecture、roadmap |
| `data/` | LLVM Organizationとmonorepoの調査snapshot |
| `toy-llvm-language/` | KofuMini frontend、KIR、LLVM emitter、tests |
| `labs/` | dominance、instruction selection、linear scan |
| `bench/` | LLVM比較benchmarkのprotocolとrunner |
| `scripts/` | 全体checkとdemo |

## 重要な結論

「LLVMを超える」を全CPU・全言語・全optimizationの総合点で定義すると、個人projectとして検証不能です。このrepositoryでは、Kofunが持つownership・effect・closed-world情報を維持し、次の限定軸で勝つ方針を採ります。

- development buildのcompile latencyとpeak RSS
- x86-64/AArch64の限定profileにおけるdeterministic codegen
- incremental function-level rebuild
- checked arithmeticとownership semanticsの保持
- direct ELF64/PE32+/Mach-O生成によるlinker不要のpath
- passごとのtranslation validation
- Kofun固有workloadでのcode sizeとruntime

Release buildではLLVMを比較oracle兼optional backendとして残します。独自backendにsilent fallbackしません。

## 検証状態

- Python frontend/KIR/interpreter/emitter tests: 常時実行
- LLVM IR assemble/verify: `llvm-as`/`opt`が存在するとき実行
- native compile/run: `clang`が存在するとき実行
- 現在の作成環境にはLLVM toolchainがないため、native testはskipとして明示されます

調査sourceは[Sources](docs/SOURCES.md)に一次資料中心でまとめています。
