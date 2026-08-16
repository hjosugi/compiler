# LLVM backend内部

ここでのbackendは狭義の「LLVM IRからtarget machine codeまで」です。Clangなどのfrontend、LLVM middle-end、LLD/runtimeまで含む全体は別章と接続します。

## 1. 入力契約: LLVM IR

LLVM IRはtyped SSA、basic block、明示的CFGを持ちます。整数は`iN`、pointerはopaque `ptr`、vectorは固定長またはscalableです。重要なのはsyntaxよりsemanticsです。

- `undef`、poison、freezeは別物。
- `nsw`/`nuw`違反はsource言語の普通のoverflowとは異なる結果を生む。
- pointer provenance、alignment、dereferenceable、alias metadataは最適化契約。
- `inbounds` GEPにも意味論上の条件がある。
- target tripleとdata layoutがsize、alignment、address spaceを決める。

frontendは「LLVMが受理するIR」ではなく「source semanticsと同値なIR」を生成する必要があります。

## 2. Middle-end

典型的な流れはcanonicalization、scalar optimization、loop optimization、interprocedural optimization、vectorization、cleanupです。実際のpipelineはoptimization level、LTO、PGO、targetで変わります。

| 分類 | 例 | 目的 |
|---|---|---|
| canonicalization | mem2reg、SROA、instcombine、simplifycfg | 後続passが扱いやすい形にする |
| scalar | GVN、SCCP、DCE、LICM | 冗長計算・不要codeを除く |
| loop | rotate、unroll、unswitch、indvars | loop構造を変換する |
| vector | loop vectorizer、SLP | SIMD命令へまとめる |
| interprocedural | inliner、globalopt、IPSCCP | 関数境界を越えて最適化 |
| memory | AA、MemorySSA利用pass | load/storeの依存を判断 |

New Pass Managerはanalysis結果をanalysis managerへcacheし、preserved analysisを明示します。公式文書上、middle-endはNew PMへ移行していますが、machine codegen pipelineはlegacy PMを使う部分が残ります。pass順序は単なる一覧ではなく、相互作用する設計です。

## 3. Target-independent code generation

LLVM IRは無限個のSSA virtual valueを持つ一方、CPUは有限register、複雑なoperand制約、flag register、calling conventionを持ちます。CodeGenはこの差を埋めます。

### Instruction selection path

| Path | 特徴 | 向く場面 |
|---|---|---|
| SelectionDAG | 成熟したDAG combiningとpattern selection | 多くのproduction target、最適化品質 |
| FastISel | 対応patternを高速に直接選ぶ | `-O0`などcompile latency重視 |
| GlobalISel | generic MIRを段階的にlegalize/select | pipelineの明確化、新target、global reasoning |

GlobalISelの主要段階:

1. IRTranslator: LLVM IRをgeneric MIRへ変換
2. Legalizer: targetが扱えないtype/opを分解・拡張・library call化
3. RegBankSelect: general/vector/flagなどregister bankを割り当て
4. InstructionSelect: generic opcodeをtarget opcodeへ選択

selection後もpseudo instruction展開、machine optimization、register allocation、schedulingが続きます。

## 4. MIRとMachineFunction

MIRではfunction、machine basic block、virtual/physical register、frame index、register class、machine operand、memory operandを表現します。LLVM IRのtypeだけでは足りず、target constraintを段階的に付与します。

観察command例:

```bash
llc -stop-after=irtranslator input.ll -o -
llc -stop-after=legalizer input.ll -o -
llc -stop-before=greedy input.ll -o -
llc -verify-machineinstrs input.ll -o /dev/null
```

pass名はversion/targetで変わり得るため、`llc --print-passes`とdebug outputで確認します。

## 5. Register allocation

livenessからlive intervalを構築し、virtual registerをphysical registerへ写します。足りなければspill/reloadを挿入します。

| allocator/考え方 | trade-off |
|---|---|
| fast/local | compileが速いがspillが増えやすい |
| basic | 教育・基準向け |
| greedy | LLVMの代表的production allocator。split、eviction、coalescing等 |
| PBQP | 複雑な制約をgraph problemとして扱う選択肢 |

難所はsubregister、two-address、fixed register、call-clobber、register mask、rematerialization、stack slot coloring、debug value維持です。`labs/linear_scan.py`は中心概念だけを切り出しています。

## 6. Schedulingとhazard

instruction schedulingはdependencyを守りながらlatencyを隠し、execution resource競合を減らします。pre-RAはregister pressureを、post-RAはphysical制約とhazardを考慮します。target scheduling modelはinstruction latency、resource usage、micro-op等を記述し、`llvm-mca`でsteady-state throughputを分析できます。

## 7. MC layerとobject emission

MC layerはMachineInstrより低いMCInst、operand、fixup、fragment、section、symbolを扱い、assembly printerまたはobject writerへ流します。

```text
MachineFunction
  -> target pseudo expansion / lowering
  -> MCInst
  -> instruction encoding + fixup
  -> ELF / COFF / Mach-O object
  -> linker
```

relocationは未確定symbol addressをlink時に解決する記録です。branch range、relaxation、PIC/GOT/PLT、TLS modelはtarget/object format/linkerと跨る問題です。

## 8. Target実装の構造

`llvm/lib/Target/<Target>/`には通常、次が置かれます。

- target machineとsubtarget/feature解析
- calling convention lowering
- instruction/register定義
- SelectionDAG loweringまたはGlobalISel
- frame lowering、prologue/epilogue
- assembly printer/parser、disassembler
- scheduling model、target transforms

TableGen `.td`はinstruction、register、calling convention、pattern、subtarget feature等からC++ tablesを生成します。TableGenだけでbackendが完成するわけではなく、不規則なlegalization、ABI、pseudo expansionは手書きlogicを必要とします。

## 9. Profile、LTO、ML、post-link

- instrumentation/sample PGO: branch frequency、value profileをpassへ与える。
- ThinLTO: summaryにより分散・incremental性を保ちながらcross-module optimization。
- Full LTO: moduleを大きく統合し、より広いoptimization機会を得る。
- MLGO: heuristicの一部をtrained modelで置換する枠組み。公式資料ではsize向けinliningとperformance向けregister allocation evictionが主な対象。
- BOLT: linked binaryとprofileを使い、basic block/function layout等をpost-link最適化。

これらは独立ではありません。build time、profile代表性、binary layout、debug/unwind correctnessを一緒に測ります。

## 10. LLVMの強さと弱さ

強さ:

- target、ABI、object format、debug ecosystemの広さ
- 多数のfrontendで検証された汎用IR/pass
- vectorization、LTO、PGO、sanitizer、JIT、linkerとの統合
- test-suite、LNT、fuzzer、release branchによる品質基盤

弱さ/設計上のtrade-off:

- 巨大なbuild時間・memory・学習面積
- LLVM IRまで早くlowerするとownership、effect、tensor shapeなどが失われる
- optimization contractとUB/poisonをfrontendが正確に扱う必要
- 汎用性のため、特定言語・特定workloadに最適なcompile latencyではない
- version間API/IR/pipeline変化をembedderが吸収する必要

したがってKofunはLLVMを捨てるのではなく、LLVM backendをcorrectness/performance oracleとして維持しつつ、fast direct backendとhigh-level KIRを競わせます。

