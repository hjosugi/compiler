# 実装roadmap

期間は人数ではなくdependency順を示します。各phaseはexit criteriaを満たすまで次へ進みません。

## Phase 0: Language contract

- lexical grammar、typed AST、error model
- integer/FP overflow、evaluation order、panic semantics
- module/name resolution、public ABI方針
- executable reference interpreter

Exit: language conformance testとrandom well-typed generatorがある。

## Phase 1: KIR foundation

- HIR→KIR-S→typed SSA KIR-O
- CFG/dominance/use-def/type/phi verifier
- deterministic serializer、text parser/printer round-trip
- interpreterとpass manager、analysis cache

Exit: every pass前後でverifyし、round-trip/differentialが通る。

## Phase 2: LLVM production path

- correct LLVM IR semantics、debug locations
- runtime ABI、C FFI、sanitizer hooks
- O0/O2、ThinLTO、PGO profile
- LLVM version adapterとCI matrix

Exit: supported language corpusがnativeでreferenceと一致する。

## Phase 3: x86-64 baseline

- generic MIR、legalizer、x86-64 selector
- System V calling convention、linear scan、frame lowering
- assembly text backend、system assembler/linker
- disassembly-based tests

Exit: integer/control/function subsetがLLVM/directで一致し、latency benchmarkを公開。

## Phase 4: Object writerとdebug

- ELF64 relocatable、symbol、relocation
- DWARF line、basic unwind、LLD/system linker integration
- content-addressed function cache、deterministic output

Exit: clean/incremental reproducibilityとdebugger smoke test。

## Phase 5: Optimization

- SCCP、DCE、GVN、simplify CFG
- ownership alias/escape、stack promotion
- scheduling、live range split、rematerialization
- bounded e-graph/local superoptimizer + validator

Exit: correctness gateを維持し、LLVM O2へのquality gapをraw dataで報告。

## Phase 6: AArch64

- AAPCS64、register/vector、instruction encoding
- Mach-OまたはELF優先順位を決める
- atomic、PIC/TLS、unwind/debug

Exit: target conformance、cross/native CI、differential complete。

## Phase 7: Profile-driven optimizer

- instrumentation/sample profile schema
- function/block layout、inlining、specialization budget
- cost model versioning、retraining/reproducibility
- post-link layoutとの責任分担

Exit: held-out corpusで事前登録したtargetを評価。

## GitHub milestone案

| Milestone | Issue例 |
|---|---|
| `M0-semantics` | spec、interpreter、diagnostic、fuzzer |
| `M1-kir` | verifier、printer/parser、dominance、pass manager |
| `M2-llvm` | emitter、runtime ABI、debug、CI toolchain |
| `M3-x64-asm` | legalize、isel、regalloc、SysV、asm printer |
| `M4-elf-cache` | encoder、ELF、relocation、incremental cache |
| `M5-opt` | scalar/ownership optimization、validation |
| `M6-aarch64` | AAPCS64、encoder、object/debug |

各issueにsemantic change、IR before/after、test、benchmark impact、unsupported caseを記載します。performance PRはcorrectness resultとraw benchmarkを必須にします。

