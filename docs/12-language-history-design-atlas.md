# 言語史・compiler系譜・設計atlas

目的は名前を暗記することではなく、「どの問題に、どの意味論と実装方式が選ばれ、何を支払ったか」を言語設計へ再利用することです。世界中の実験言語を完全列挙することは不可能なので、設計上の分岐を生んだ言語と、現在も重要なcompiler familyを系統別に網羅します。

## 1. 大きな歴史の流れ

| 時代 | 代表 | compiler/runtime上の転換 | 設計への示唆 |
|---|---|---|---|
| 1940s–50s | machine code、assembly、Fortran | symbolic assembly、最初期の最適化compiler | 高級表現でも十分よいcodeを自動生成できる |
| 1958–60s | Lisp、ALGOL、COBOL | GC、再帰、lexical block、BNF、portable business language | syntax、memory、domainの選択は別軸 |
| 1970s | C、Pascal、Smalltalk、Prolog、ML | portable systems language、VM/OO、logic、型推論 | 実行modelが言語の表面設計を規定する |
| 1980s | C++、Objective-C、Erlang、Self | zero-overhead abstraction、message passing、prototype、JIT研究 | static specializationとdynamic feedbackの二方向 |
| 1990s | Haskell、Python、Ruby、Java、JavaScript | lazy purity、scripting、portable bytecode VM、GC、JIT | productivityとdeploymentをruntimeで解く |
| 2000s | C#/.NET、LLVM、CUDA | common managed IL、reusable optimizing backend、GPU compute | frontend/backend分離とdomain-specific target |
| 2010s | Go、Rust、Swift、Kotlin、Julia、WebAssembly | fast builds、ownership、progressive lowering、multiple dispatch JIT、portable sandbox | safety・latency・interopを第一級の目標にする |
| 2020s | MLIR ecosystem、Mojo系、Wasm components、verified compilation | multi-level IR、AI accelerator、capability/component model、検証 | 1つの低水準IRだけでは情報保持が足りない |

年代は「最初の公開・普及期」の概略です。language versionの年表ではありません。

## 2. 主要系統をcompiler視点で比較

| 系統・言語 | 型/意味論 | memory/runtime | 代表pipeline | 借りる点 | 注意点 |
|---|---|---|---|---|---|
| Fortran | static、array/numerical | native、manual中心 | high-level loop/array解析→native | alias制約とarray意味論を最適化へ渡す | 古い互換性が設計を拘束 |
| C | weakly static、低水準、UBあり | manual | AST→SSA IR→machine | ABI、FFI、predictable layout | UB依存最適化は安全言語の意味と衝突 |
| C++ | generic、RAII、zero-overhead志向 | deterministic destruction | template instantiation→LLVM/GCC | value semantics、RAII、compile-time計算 | 文法・overload・templateが巨大な複雑性を生む |
| Ada/SPARK | strong static、contract | native、制御可能 | semantic analysis→native/proof | contract、range、safety-critical profile | feature集合とimplementation負担が大きい |
| Lisp/Scheme | dynamic、homoiconic、closure | GC | forms→macro expansion→bytecode/native | syntaxをdataとして扱うmacro、REPL | unrestricted macroはtoolingと解析を難化 |
| Smalltalk | dynamic、message send、image | GC、VM/JIT | bytecode→profile JIT | live image、uniform object model | startup/memory、FFI、静的予測 |
| Self | prototype、dynamic | optimizing VM | feedback→maps/shapes→speculative JIT | inline cache、deopt、型feedback | VM/backendが非常に複雑 |
| ML/OCaml | HM型推論、ADT、pattern match | tracing GC | typed lambda→bytecode/native、Flambda | algebraic data type、exhaustiveness、module | inferenceとabstraction境界のerror説明 |
| Haskell/GHC | pure、lazy、type class | GC、graph reduction | Core→STG→Cmm→native/LLVM | small typed core、effect分離、rewrite rules | laziness、boxing、runtimeのcost modelが難しい |
| Prolog | logic、unification、backtracking | WAM系VM/GC | clauses→WAM-like instructions | declarative relation、pattern-driven execution | controlとperformanceの予測性 |
| Erlang/BEAM | dynamic、actor、immutable中心 | process-local GC、VM/JIT | Core Erlang→BEAM bytecode→JIT | fault isolation、mailbox、supervision | message copy、latency/throughput trade-off |
| Java/JVM | nominal static、managed | GC、verification、tiered JIT | source→bytecode→interpreter/C1/C2 | stable bytecode、verification、adaptive JIT | warmup、GC、object overhead |
| C#/.NET | static、generic、managed+unsafe | GC、tiered RyuJIT/AOT | CIL→quick JIT→optimized JIT | reified genericとの折衷、metadata、async lowering | runtime surfaceとcompatibility burden |
| Python/CPython | dynamic、object model | refcount+cycle GC、VM | AST→bytecode→adaptive interpreter/JIT実験 | simple semantics、inspection、巨大ecosystem | object/dispatch cost、GIL/ABI互換性 |
| Ruby/YARV | dynamic、open class、block | GC、bytecode/JIT | AST→YARV bytecode→YJIT/MJIT系 | developer ergonomics、block/DSL | monkey patchingがglobal optimizationを制限 |
| JavaScript/V8 | dynamic、prototype、speculative | GC、tiered JIT | Ignition→Sparkplug→Maglev→TurboFan | tiering、hidden class、deoptimization | observable semanticsとweb互換性の巨大負担 |
| Lua/LuaJIT | dynamic、小型VM | GC、bytecode/trace JIT | bytecode→trace specialization | embedding、小さいruntime、trace JIT | trace exitとunpredictable workload |
| Go | static、structural interface | GC、goroutine runtime | typed IR→generic SSA→target rules | build速度、単純なtoolchain、stack growth | GCとinterface dispatch、言語機能を意図的に制限 |
| Rust | ownership、trait、algebraic types | GCなし、RAII | AST/HIR→MIR→monomorphize→LLVMほか | ownership facts、MIR safety checks、no-GC safety | compile latency、lifetime/trait diagnostics |
| Swift | value semantics、protocol、ARC | ARC+runtime | AST→SIL→LLVM | ownership-aware SIL、progressive lowering | generics/interop/ARC optimizationの複雑性 |
| Kotlin | nullable type、JVM/native/JS | target依存 | common frontend/IR→JVM/LLVM/JS | multiplatform IR、null safety | 各target semanticsとinteropの共通化 |
| Zig | explicit allocation/error、comptime | GCなし | AST/ZIR→AIR→LLVMまたはdirect backend | cross compilation、comptime、fast debug backend | comptime resource control、backend間品質差 |
| Julia | dynamic multiple dispatch | GC、specializing JIT | lowered IR→type inference/SSA→LLVM JIT | type-driven specialization、introspection | latency、code explosion、invalidations |
| WebAssembly | typed stack machine | sandbox、host runtime | source IR→Wasm→validation→tiered JIT/AOT | portable verified target、capability境界 | low-level GC/exception/host integration choices |
| CUDA/SPIR-V | SIMT、kernel | device memory/runtime | domain IR→PTX/SPIR-V→driver compiler | hierarchyとmemory spaceをIRに保持 | hardware vendor差、host-device coordination |
| SQL/query engines | relational/declarative | database runtime | logical plan→cost-based physical plan→vector/JIT | rule+cost最適化、statistics | cost model誤差、semantic null/ordering |

## 3. Compiler構成の代表pattern

### AOT native

C、C++、Rust release、Goなど。deploymentが単純でstartupが速い一方、実行時の型・hotnessを直接利用しにくいです。PGOはその差を埋めます。

### Bytecode VM

CPython、Ruby、OCaml bytecode、BEAMなど。compilerが簡単、portable、inspectionしやすい反面、dispatch overheadがあります。bytecodeは「将来変えない公開形式」か「versionごとに変えてよい内部形式」かを最初に決めます。

### Tiered JIT

HotSpot、.NET、V8。interpreter/quick compilerですぐ起動し、profileを収集してhot codeだけ高度最適化します。必要部品はcode cache、safepoint、stack map、OSR、deoptimization、GC協調です。AOT backendよりruntimeが主役になります。

### Trace JIT

LuaJITなど。hot loopの実行traceを直線化しspecializeします。動的言語のloopに強い一方、分岐が多いcodeやtrace explosionへの対策が必要です。

### Multi-level lowering

Swift SIL、Rust HIR/MIR、GHC Core/STG/Cmm、MLIR。source固有情報を持つhigh IRからmachine寄りIRへ少しずつ制約を確定します。「最初からLLVM IRへ落とす」と失うownership、effect、shape、generic情報を各levelで活用できます。

### Verified / translation-validated

CompCertはproofされたpassを合成し、Alive2は個々のLLVM IR変換を検証する方向です。全compilerの証明が難しい場合も、IR semanticsを形式化し、passごとのwitnessやtranslation validationを段階導入できます。

## 4. 言語設計の選択表

### 型

| 選択 | 強み | cost |
|---|---|---|
| dynamic | 対話性、柔軟なmetaprogramming | runtime check、JIT/VM複雑性 |
| nominal static | API境界とdiagnosticが明確 | wrapper/boilerplate |
| structural static | compositionが柔軟 | compatibility判定とerrorが複雑 |
| HM inference | 簡潔で強い型 | subtyping/effect/overloadとの統合 |
| dependent/refinement | 強い仕様表現 | type checking、termination、error説明 |
| gradual | 段階的移行 | runtime cast境界とsoundness設計 |

Kofun案: local inferenceは行うがpublic APIは型注釈必須。nominal data type、structural effect、traitはcoherence規則を持たせる。最初からsubtypingを広く入れない。

### Memory

| 方式 | 強み | cost |
|---|---|---|
| manual | 小runtime、完全な配置制御 | use-after-free、leak |
| tracing GC | cyclic graphと簡潔なAPI | pause、runtime、FFI barrier |
| reference counting/ARC | destruction時点が比較的明確 | cycle、atomic count、retain/release最適化 |
| ownership/borrow | GCなしで静的安全 | alias/lifetime規則と学習負担 |
| region/arena | 高速一括解放 | lifetime粒度、長寿命参照 |

Kofun案: ownershipをdefaultにし、arenaを標準抽象、shared heapは明示型にする。backendまでunique/shared/escaped factsを落とさない。

### Errorとeffect

- exceptionはhappy pathを簡潔にするが、unwind ABI、hidden control flow、optimizationを複雑にする。
- result typeはcontrol flowを明示するが、伝播syntaxが必要。
- algebraic effectはeffect polymorphismとhandler loweringが必要。

Kofun案: recoverable errorはtyped resultと`?`、panicはabortをdefault。effect setをfunction signatureに残し、pure/noalloc/nothrowを最適化契約に使う。

### Generic

- monomorphization: 高速化しやすいがcompile time/code sizeが増える。
- type erasure/dictionary: codeを共有できるがindirectionが増える。
- reified runtime generic: reflectionに強いがruntime/compiler契約が広い。

Kofun案: size/primitive-specializedとshared dictionaryのhybrid。profileとcode-size budgetで選び、ABIにはstrategyを固定しすぎない。

### Concurrency

- OS thread+shared memory: ecosystemとnative interopに強い。
- actor: isolationとfault containmentに強い。
- async/await: I/O scalabilityに強いがstate machineとpin/cancellation semanticsが必要。
- CSP/goroutine: channel中心で書きやすいがscheduler/runtimeが必要。

Kofun案: structured concurrencyとtask lifetimeを型/regionへ接続し、data race freedomをownershipから導く。schedulerは言語仕様と実装policyを分離する。

## 5. Kofunが各言語から借りるもの

| Source | 採用候補 | そのまま採用しないもの |
|---|---|---|
| C | stable ABI、layout制御、FFI | unchecked pointerをdefaultにしない |
| C++ | RAII、value semantics、zero-overhead目標 | implicit conversionと複雑なoverload |
| ML/Rust | ADT、pattern exhaustiveness、typed IR | errorが難解になる過度な推論 |
| Swift | ownership-aware high IR | ARCを唯一のmemory modelにしない |
| Go | fast toolchain、single command、cross build | high-level意味を速さのために捨てない |
| Zig | comptime、explicit allocation、direct backend | compile-time実行の無制限なresource消費 |
| Haskell/GHC | small typed core、effect意識、rewrite rules | lazy evaluationをdefaultにしない |
| JVM/.NET/V8 | tiering、profile、deoptの知見 | v1から巨大VMを作らない |
| Julia | specializationとIR introspection | latency/code explosionを放置しない |
| Wasm | validation、portable sandbox、component境界 | native targetのcapabilityを最小公分母化しない |
| CompCert/Alive2 | semanticsとpass検証 | 最初から全proof完成を前提にしない |

## 6. 歴史から見える失敗pattern

1. syntaxの便利機能を、lowering・debug・tooling costなしで追加する。
2. source semanticsを曖昧にしたままLLVMのUB/poisonへ委ねる。
3. 1つのIRでmacroからregister allocationまで表現する。
4. genericを常にmonomorphizeし、build latencyとbinary sizeを測らない。
5. runtime ABIを早期に固定し、GC/async/exceptionの変更不能点を増やす。
6. benchmark 1個で「高速」と宣言し、compile time、RSS、size、warmupを隠す。
7. C互換を表面syntaxだけで考え、layout、calling convention、unwind、TLSを後回しにする。
8. error message、incremental dependency、IDE queryをcompiler architectureに含めない。

## 7. 読み比べる実装順

1. KofuMini: frontendとSSAの最小形
2. QBE/Cranelift: 小型backendと高速codegen
3. Go compiler: rule-based SSA backendとbuild latency
4. Rust MIR/Swift SIL: ownershipをhigh IRで扱う方法
5. GHC Core/STG/Cmm: 言語意味を複数IRで段階的に消す方法
6. V8/HotSpot/.NET: tiering、profile、deoptimization
7. MLIR: dialect、conversion、target-specific multi-level lowering
8. LLVM: 汎用最適化とtarget coverageの最大規模
9. CompCert/Alive2: correctnessをarchitectureにする方法

一次資料へのlinkは[SOURCES.md](SOURCES.md)にまとめています。各compilerは動く仕様書でもありますが、実装detailとlanguage specificationを混同しないでください。

