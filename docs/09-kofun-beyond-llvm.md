# Kofun: 限定軸でLLVMを超えるbackend設計

## 結論

LLVMの全target・全optimization・全ecosystemを総合的に超える計画は検証不能です。Kofun固有のsemantic情報、限定target、bounded optimization budgetを使い、development latency、memory、determinism、incremental rebuild、checked/ownership workloadで勝つ計画にします。

## Architecture

```text
Source
  -> HIR: names, types, generics, effects
  -> KIR-S: ownership, borrows, drops, checked operations
  -> KIR-O: typed SSA, explicit memory/effects/traps
  -> two backends
       A. LLVM IR -> LLVM release codegen
       B. generic MIR -> target MIR -> encoder/object
```

| Layer | 捨ててはいけない情報 |
|---|---|
| HIR | source span、generic/effect、diagnostic origin |
| KIR-S | unique/shared、region、escape、drop order、panic behavior |
| KIR-O | SSA、memory token/alias class、trap condition、range |
| generic MIR | legal type、calling-convention intent、value location class |
| target MIR | physical constraint、feature、frame、relocation |

## 差別化する6点

### 1. Fast baseline backend

function単位、single-pass lowering、linear-scan、local peephole、parallel codegen、direct object cacheを使います。debug buildで高価なglobal optimizationを行いません。

### 2. Ownership-aware alias optimization

unique borrow、non-escaping arena、readonly sharedをKIR-Oまで保持します。generic LLVM IRへ曖昧なmetadataを付ける前に、load elimination、stack promotion、ARC不要化をsource semanticsに基づき行います。

### 3. Explicit trap semantics

overflow、bounds、division、panicをfirst-class IR operationにし、poison/UBへ暗黙変換しません。trap merging/hoistingはobservable order規則を満たす場合だけ行います。

### 4. Deterministic incremental unit

function KIRをcanonical serializeしてcontent hashを作り、ABI/target/options hashと共にcache keyにします。symbol order、parallel schedule、hash map iterationでbinaryが変わらない設計にします。

### 5. Bounded equality saturation/superoptimization

hot blockまたはsmall pure regionだけe-graph/local enumerative searchを使い、node/time budgetを設定します。rewriteごとにsemantic preconditionを持たせ、extract後にtranslation validationします。

### 6. Multi-objective profile policy

runtimeだけでなくcompile budget、size、energy proxy、I-cache pressureをcostにします。model/heuristicのversionをartifactへ記録し、再現可能にします。

## 数値目標は仮説

以下は未達成のengineering targetで、実績ではありません。

| Milestone | Corpus/比較 | Target |
|---|---|---|
| baseline v1 | x86-64 Kofun corpus、LLVM O0 | cold compile median 5倍高速、peak RSS 70%減 |
| quality v1 | 同corpus、LLVM O2 | runtime geomean +15%以内、size +10%以内 |
| optimizer v2 | ownership/arena corpus、LLVM O2 | runtime geomean同等、選定workloadで5%以上改善 |
| incremental | 1 function edit | p95 100 ms未満（指定reference machine） |
| correctness | random+differential | known miscompile 0、seed/失敗全公開 |

hardwareとcorpusはbenchmark manifestで固定します。targetを変えて達成扱いにしません。

## LLVMを残す理由

- frontend/KIRのreference backend
- 未対応targetのportable path
- release-max、PGO/LTO/BOLTの利用
- direct backendとのdifferential oracle
- LLVM IR ecosystem/sanitizer/debug integration

backend選択は明示flagにし、direct backendがunsupportedならerrorにします。自動LLVM fallbackは測定と品質判定を壊します。

## 最大risk

| Risk | 対策 |
|---|---|
| ABI/ISA scope explosion | x86-64 SysVから開始、feature matrixをversion化 |
| miscompile | interpreter、LLVM、directの三者比較、毎pass verifier |
| optimizationが増えbuild遅延 | pass budget、profile別pipeline、timeout |
| LLVMに結局勝てない | latency/memory/incrementalを主戦場に固定 |
| IR変更でcache/ABI破損 | schema/version、migrationではなくcache invalidate |
| benchmark gaming | corpus governance、raw data、negative result公開 |

