# 正しさとperformance検証

compilerの最優先条件は「速いこと」ではなくsemantic preservationです。最適化は入力programと同じobservable behaviorを保つ必要があります。

## Test pyramid

| 層 | 方法 | 見つける問題 |
|---|---|---|
| unit | lexer/parser/type/passの小test | 局所logic、diagnostic |
| golden | AST/KIR/LLVM IR snapshot | 意図しない出力変化 |
| verifier | IR invariantを毎pass後検査 | malformed IR、SSA/CFG破壊 |
| integration | compile→link→run | ABI、toolchain統合 |
| differential | interpreter/LLVM/directを比較 | miscompile |
| randomized | grammar/type guided generation | 人が考えない組合せ |
| metamorphic | 等価変形前後を比較 | oracle不要の不整合 |
| conformance | language spec cases | 仕様逸脱 |
| ecosystem | real packagesをbuild/test | scale、compatibility |

undefined behaviorを含むC random testは比較対象が難しいため、Csmith/YARPGenの生成制約を理解します。Kofunでは言語semanticを明確にし、random generatorもwell-typed/trap outcomeを生成します。

## Pass correctness

- CompCert: compiler passのsemantic preservationをproof assistantで証明する代表。
- Alive2: LLVM IR optimizationのtranslation validation。
- VeriISLE: Cranelift instruction selection rule検証の方向。
- differential: independent implementationとの結果比較。

Kofunの現実的な順番は、形式化したKIR interpreter、pass verifier、differential test、Alive2型のlocal validator、重要passのproofです。proofしていない領域を明示します。

## Benchmarkの4軸

1. compiler: wall/cpu time、peak RSS、incremental latency、cache hit。
2. artifact: text/data/total size、relocation、debug size。
3. program: wall/cpu、cycles、instructions、cache miss、allocation。
4. quality: compile成功率、test pass、miscompile/crash、debug quality。

JITはstartup、warmup curve、steady state、code cacheも分けます。AOTとJITをsteady-stateだけで比較しません。

## Reproducible protocol

- machine、firmware、OS、governor、thermal条件を記録
- toolchain version/commitと全flagsを固定
- clean/cached buildを分離
- corpusをversion管理し、micro/real-worldを分ける
- correctness通過caseだけperformance集計
- warmup後に複数回取り、median、分散、confidence intervalを示す
- timeout/OOM/compile failureを除外せず報告
- raw JSONを保存してchartの再生成を可能にする

`bench/runner.py`はKofuMiniをreference実行し、ClangがあればLLVM IRから各optimization levelのnative binaryを作り、compile time、size、runtime、結果一致をJSONへ記録します。

## 「LLVM超え」gate

| Gate | 合格条件 |
|---|---|
| correctness | corpus全件でreferenceとstdout/exit/trap一致 |
| robustness | random testでcrash/miscompile 0、seed公開 |
| latency | 指定hardwareでLLVM baselineより目標倍率を達成 |
| memory | peak RSS target内 |
| runtime | LLVM O2に対するgeomean regression budget内 |
| size | text/total size budget内 |
| reproducibility | raw result、commit、flags、environment公開 |

目標に届かない結果もrelease noteへ載せます。benchmarkを変更したら過去値と直接比較できないことを明示します。

