# Kofun shared KIR / optional LLVM issue pack

## Purpose and safety

これは`kofun-lang/kofun`へ渡すためのlocal planning draftです。このrepositoryからIssueを自動作成しません。番号`I1`–`I12`は依存関係を表すplaceholderであり、実際に登録するときはauthoritativeな`main`と既存Issueを再監査し、real issue numberへ置換してください。

Snapshot: 2026-08-16、`kofun-lang/kofun@075fbb241367c27863c74f3884989ba7ddbbfa5b`。

既存labelは`area:compiler`、`area:backend`、`area:codegen`、`kind:implementation`、`kind:test-quality`、`P1/P2`、`size:S/M/L`、`ready/blocked/curated`です。`area:kir`と`kind:design`が必要なら、repository ownerが命名規約を確認してから作成します。

## Dependency graph

```text
I1 RFC/KIR contract
 +-> I2 semantic frontend boundary
 +-> I3 serialization/verifier/hash
      +-> I4 C11 first consumer
           +-> I5 direct-native consumer
           +-> I6 wasm32 consumer
           `-> I10 optional LLVM emitter

I7 differential harness -----> I4/I5/I6/I10 acceptance
I8 benchmark protocol -------> I10 comparison claim
I9 determinism CI -----------> I3/I4/I5/I6
I11 musttail validation -----> I3 + each backend
I12 incremental cache spike -> I3 hashes + I4 first consumer
```

I7–I9 and the test design of I11 can start before the migration issues, using current bounded backends as fixtures.

---

## I1 — RFC-0019: KIR v1 semantic, serialization, and hash contract

Labels: `area:compiler`, proposed `area:kir`, proposed `kind:design`, `P1`, `size:L`, `curated`.

Goal: accept one versioned contract for KIR-H/KIR-M, required source semantics, canonical serialization, function/module hash, required-feature negotiation, and backend fail-closed behavior.

Acceptance:

- Specify ownership/alias facts, effects/authorities, checked numerics, ADT/match, generic identity, cleanup, ABI, tail/musttail.
- Define canonical bytes and semantic versus diagnostic fields.
- Define function, module, interface, and backend cache-key digests.
- Include malformed and unknown-feature behavior.
- State explicitly that LLVM IR is a lowering target, not KIR semantics.

Blocked by: none. Blocks: I2–I6, I10, I12.

## I2 — One typed frontend boundary producing KIR-H

Labels: `area:compiler`, `kind:implementation`, `P1`, `size:L`, `curated`, `blocked`.

Goal: make lexer/parser/name resolution/type/ownership/effect checking a single producer rather than duplicating bounded parsing in C11/native/wasm.

Acceptance:

- One source program has one resolved symbol/type/ownership result independent of target.
- Unsupported backend shape is diagnosed after the shared frontend and names the selected backend.
- No target probes or installed tools change frontend semantics.
- Existing capability matrix remains honest during migration.

Blocked by: I1.

## I3 — Canonical KIR serializer, parser, verifier, and content hashes

Labels: proposed `area:kir`, `kind:implementation`, `P1`, `size:L`, `curated`, `blocked`.

Goal: implement machine-readable KIR v1 with round-trip, verifier, module/function/interface digest, and deterministic dump.

Acceptance:

- Round-trip preserves canonical bytes.
- Verifier rejects use-before-def, non-dominating use, type mismatch, incomplete phi, invalid ownership state, unknown required feature.
- Function order, process, path, locale, and job count determinism corpus passes.
- One-function edit leaves unrelated function digests unchanged.

Blocked by: I1. Blocks: I4–I6, I9–I12.

## I4 — Strangler migration: C11 as the first KIR consumer

Labels: `area:backend`, `area:codegen`, `kind:implementation`, `P1`, `size:M`, `curated`, `blocked`.

Goal: lower shared KIR to the current C11 bootstrap path while the old path remains an oracle.

Acceptance:

- Selected corpus produces matching stdout, exit/trap, and normalized diagnostics on old and KIR paths.
- Backend-specific refusal occurs without re-parsing source.
- A flag selects the explicit experimental path; no silent fallback.
- Removal condition for the old C11 frontend is documented, not executed early.

Blocked by: I2, I3, I7.

## I5 — Migrate direct native x86-64/AArch64 lowering to KIR

Labels: `area:backend`, `area:codegen`, `kind:implementation`, `P1`, `size:L`, `curated`, `blocked`.

Goal: feed both machine backends from the same verified KIR, preserving direct image output and RFC-0018 target identity.

Acceptance:

- No native source parser remains on the selected KIR path.
- Checked arithmetic, calls, branches, tail requirements, syscall/runtime boundaries have differential tests.
- ELF64/PE32+/Mach-O image writer inputs are deterministic backend artifacts.
- Unsupported operations refuse; LLVM/C11 are never fallback.

Blocked by: I3, I4, I7, I9.

## I6 — Migrate wasm32 lowering to KIR

Labels: `area:backend`, `area:codegen`, `kind:implementation`, `P1`, `size:M`, `curated`, `blocked`.

Goal: replace wasm32's bounded source parser with a KIR consumer while preserving its distinct target/runtime contract.

Acceptance:

- Same typed program reaches wasm and native backend boundary.
- Wasm validation, import/export, trap, i64, call, and control-flow tests pass.
- Host ABI requirements remain explicit KIR/backend capability, not implicit fallback.

Blocked by: I3, I4, I7, I9.

## I7 — Cross-backend differential corpus and reducer

Labels: `area:quality`, `area:compiler`, `kind:test-quality`, `P1`, `size:M`, `curated`, `ready`.

Goal: compare reference/C11/native/wasm/LLVM outcomes from one manifest and preserve every mismatch as a reduced regression.

Acceptance:

- Compare stdout, exit, trap class, and selected artifact facts separately.
- Unsupported is distinct from mismatch and success.
- Random generation stays inside declared language profiles.
- Reducer keeps the mismatch and records compiler/backend digest.

Blocked by: none for harness; backend adapters land with I4–I6/I10.

## I8 — Three-axis benchmark protocol and claim gate

Labels: `area:compiler`, `kind:test-quality`, `P1`, `size:M`, `curated`, `ready`.

Goal: measure compile latency/RSS, runtime, and binary size without hiding correctness failures.

Acceptance:

- Clean and one-function incremental builds are separate.
- Toolchain digest, target, CPU, flags, hardware, raw samples, and summary are committed artifacts.
- Mismatch/unsupported samples are excluded from performance comparison with a visible reason.
- Win conditions are workload-specific and set before measurement.

Blocked by: none for protocol; LLVM comparison depends on I10.

## I9 — KIR and artifact determinism CI matrix

Labels: `area:quality`, `area:compiler`, `kind:test-quality`, `P1`, `size:M`, `curated`, `ready`.

Goal: prove same input produces byte-identical semantic KIR and target artifacts under controlled environment variation.

Acceptance:

- Vary clean path, process, job count, locale/timezone, and discovery order.
- Compare raw bytes before any narrow documented normalization.
- First differing field/offset is reported.
- Determinism failure blocks cache/release claims.

Blocked by: none for fixture design; production gate uses I3.

## I10 — Optional `llvm-hosted-*` textual LLVM IR backend

Labels: `area:backend`, `area:codegen`, `kind:implementation`, `P2`, `size:M`, `curated`, `blocked`.

Goal: emit textual `.ll` from shared KIR for oracle, performance comparison, and optional target escape hatch.

Acceptance:

- No libLLVM/C++ binding; invoke an explicitly configured external toolchain.
- Missing LLVM rejects only the selected `llvm-hosted` target.
- Direct target never probes or falls back to LLVM.
- Stable LLVM version is pinned in benchmark/reproducer metadata and reevaluated at implementation time.
- KIR reference and LLVM native outcomes match the differential corpus.

Blocked by: I3, I4, I7. Must not claim RFC-0018 completion.

## I11 — Tail and `musttail` cross-backend conformance

Labels: `area:compiler`, `area:backend`, `kind:test-quality`, `P1`, `size:M`, `curated`, `ready`.

Goal: distinguish optional TCO from required constant-stack calls and test ABI/cleanup preconditions on every backend.

Acceptance:

- Deep recursion demonstrates bounded stack for accepted `musttail` cases.
- Signature, ownership cleanup, authority lifetime, or ABI mismatch is refused before artifact publication.
- LLVM path verifies emitted `musttail`; direct/wasm paths inspect their target form.
- No normal-call fallback for required tail semantics.

Blocked by: implementation integration uses I3 and each backend; test corpus can start now.

## I12 — Function-granular incremental cache design spike

Labels: `area:compiler`, proposed `area:kir`, proposed `kind:design`, `P2`, `size:M`, `curated`, `blocked`.

Goal: use function/interface hashes to measure a safe minimal invalidation graph before committing to an on-disk cache format.

Acceptance:

- Key includes semantic function, interface/layout, target/profile/runtime ABI, and backend implementation digests.
- One private-body edit rebuilds only affected functions; public ABI/layout edit invalidates dependents.
- Digest/corruption mismatch refuses reuse and rebuilds safely.
- Report compile time, peak RSS, bytes read/written, hit/miss reason, and deterministic artifact result.

Blocked by: I3, I4, I8, I9.

## Registration checklist

Before creating any issue:

1. Re-fetch `kofun-lang/kofun/main` and re-read compiler architecture, RFC ledger, roadmap, open compiler issues, and label set.
2. Split every `size:L` item before adding `ready` unless repository policy explicitly allows it.
3. Replace `I<N>` with real links only after all issues exist.
4. Add `blocked` only for named hard dependencies; otherwise use `ready` after Definition of Ready is met.
5. Do not close or rewrite existing Generics, Decimal, parallelism, syscall, or 1.0 tracker issues merely to make this pack green.
6. Record exact audited commit in every issue body.
