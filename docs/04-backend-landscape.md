# Compiler backend landscape

「backend」は目的が違えば勝者も変わります。peak runtime、compile latency、target数、proof、binary size、JIT warmupを1つの順位へ潰さず比較します。

| System | 主用途 | IR/方式 | 強み | 主な制約 |
|---|---|---|---|---|
| LLVM | 汎用AOT/JIT | LLVM IR→DAG/GlobalISel/MIR | target/optimization/ecosystem | size、compile latency、IR semanticsの難しさ |
| GCC | GNU language/native | GENERIC/GIMPLE SSA→RTL | language/target成熟度、system integration | reusable libraryとしての組込み方がLLVMと異なる |
| Cranelift | fast codegen/JIT/AOT | CLIF SSA→VCode | compile speed、Wasmtime production、検証/fuzz | LLVMほど広いpeak optimization/targetではない |
| QBE | 小型AOT backend | compact SSA IL | 小さく理解可能、C familyに十分な機能 | target/optimization/debug ecosystemが限定 |
| MLIR | multi-level compiler infra | dialect+conversion | domain情報を段階保持、custom accelerator | 最終machine backendそのものではなくLLVM等へ接続 |
| Binaryen | WebAssembly | Wasm IR/parallel passes | Wasm固有、fast、toolchain | native ISA汎用backendではない |
| Graal | managed/polyglot JIT | graph IR、partial evaluation | language implementation、speculation、escape analysis | VM/runtime統合の複雑性 |
| HotSpot C1/C2 | JVM tiered JIT | JVM bytecode→tiered IR | profile、deopt、成熟したmanaged runtime | warmup、code cache、GC/runtime coupling |
| .NET RyuJIT | CLI managed JIT | CIL→tiered native | quick JIT/PGO/AOT連携、runtime integration | .NET type/runtime contractに特化 |
| V8 | JavaScript/Wasm | Ignition/Sparkplug/Maglev/TurboFan | multi-tier、speculation、deopt | JS semanticsとbrowser securityの巨大complexity |
| Go compiler | Go AOT | Go IR→generic SSA→arch rules | fast builds、integrated assembler/linker | Go semanticsとtarget setに特化 |
| Zig backends | Zig/C cross build | AIR→LLVMまたはdirect | fast debug x86 backend、toolchain統合 | direct backendのtarget/optimization成熟度差 |
| GHC NCG | Haskell | Core→STG→Cmm→native | language/runtime特化、fast path | supported targetと汎用性が限定 |
| CompCert | verified C | proof-carrying passes | semantic preservation proof | language/target/optimization範囲と速度のtrade-off |
| BOLT | post-link optimizer | binary CFG+profile | layoutを実address/profileで改善 | compiler frontend/backendの代替ではない |

## 目的別の候補

- 小さな言語を最短でnative化: QBEまたはCranelift。
- 多target、最高水準のrelease optimization: LLVM/GCC。
- WebAssemblyだけ: Binaryen + Wasm runtime backend。
- tensor/accelerator/DSL: MLIR dialect + LLVM/SPIR-V/CIRCT等。
- managed dynamic language: bytecode interpreter + tiered JIT。Graal採用も検討。
- safety-critical semantic assurance: CompCert、translation validation、restricted language profile。
- milliseconds単位のdevelopment compile: custom direct backend/Craneliftをrelease backendと併用。

## 「LLVMを超えた」の正しい書き方

悪い主張: 「私たちのbackendはLLVMより速い」。

検証可能な主張例:

> x86-64 Linux、Kofun corpus v1、cold process、8 core固定、debug profileにおいて、Kofun direct backendはLLVM `-O0`よりmedian wall timeが5倍短くpeak RSSが70%小さい。生成programのruntimeは同じcorpusでLLVM `-O2`より中央値12%遅い。

必須情報はhardware、OS、toolchain commit、flags、corpus、warm/cold、回数、統計、失敗caseです。勝ったcaseだけでなくgeomean、distribution、code size、correctnessを公開します。

## Kofunの二backend戦略

| Profile | Backend | 最適化budget | 目的 |
|---|---|---|---|
| check | KIR interpreter/validator | なし | semantics、diagnostic |
| dev | direct baseline | function-local、linear | sub-second rebuild |
| release-fast | direct optimizing | bounded、profile optional | predictable memory/time |
| release-max | LLVM | LLVM O2/O3/PGO/LTO | peak performance oracle |

同じKIR semanticsを全pathで共有し、unsupported featureはcompile errorにします。silent fallbackはbenchmarkを汚し、backend bugを隠すため禁止します。

