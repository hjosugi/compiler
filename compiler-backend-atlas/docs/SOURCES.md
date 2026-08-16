# Sources and research method

調査snapshot: **2026-08-16**。GitHub repository数・stars等は変動するため、`data/`へ取得時点を固定しました。設計・実装の説明は可能な限り公式documentation、project repository、論文/verified projectを優先しています。blogのbenchmark値は普遍的な性能保証として扱っていません。

## LLVM coreとrelease

- [LLVM GitHub Organization](https://github.com/llvm)
- [llvm/llvm-project](https://github.com/llvm/llvm-project)
- [LLVM Documentation](https://llvm.org/docs/)
- [LLVM Language Reference](https://llvm.org/docs/LangRef.html)
- [LLVM Code Generator](https://llvm.org/docs/CodeGenerator.html)
- [Global Instruction Selection](https://llvm.org/docs/GlobalISel/)
- [New Pass Manager](https://llvm.org/docs/NewPassManager.html)
- [Writing an LLVM Backend](https://llvm.org/docs/WritingAnLLVMBackend.html)
- [TableGen Programmer's Reference](https://llvm.org/docs/TableGen/ProgRef.html)
- [Machine IR format](https://llvm.org/docs/MIRLangRef.html)
- [LLVM Code Generator: MC layer](https://llvm.org/docs/CodeGenerator.html#the-mc-layer)
- [LLVM releases](https://releases.llvm.org/)
- [LLVM 22.1.8 release](https://github.com/llvm/llvm-project/releases/tag/llvmorg-22.1.8)
- [LLVM 23.1.0-rc3 release](https://github.com/llvm/llvm-project/releases/tag/llvmorg-23.1.0-rc3)

## Optimization、profile、quality

- [LLVM Alias Analysis](https://llvm.org/docs/AliasAnalysis.html)
- [LLVM MemorySSA](https://llvm.org/docs/MemorySSA.html)
- [LLVM Loop Terminology](https://llvm.org/docs/LoopTerminology.html)
- [LLVM Vectorizers](https://llvm.org/docs/Vectorizers.html)
- [LLVM PGO](https://llvm.org/docs/HowToBuildWithPGO.html)
- [ThinLTO](https://clang.llvm.org/docs/ThinLTO.html)
- [MLGO](https://llvm.org/docs/MLGO.html)
- [BOLT](https://github.com/llvm/llvm-project/tree/main/bolt)
- [llvm-mca](https://llvm.org/docs/CommandGuide/llvm-mca.html)
- [llvm-exegesis](https://llvm.org/docs/CommandGuide/llvm-exegesis.html)
- [LLVM Test Suite](https://github.com/llvm/llvm-test-suite)
- [LNT](https://github.com/llvm/llvm-lnt)
- [LLVM Buildbot infrastructure](https://github.com/llvm/llvm-zorg)

## LLVM subprojectsとMLIR ecosystem

- [Clang](https://clang.llvm.org/)
- [LLD](https://lld.llvm.org/)
- [LLDB](https://lldb.llvm.org/)
- [Flang](https://flang.llvm.org/)
- [compiler-rt](https://compiler-rt.llvm.org/)
- [MLIR](https://mlir.llvm.org/)
- [MLIR rationale](https://mlir.llvm.org/docs/Rationale/Rationale/)
- [MLIR language reference](https://mlir.llvm.org/docs/LangRef/)
- [CIRCT](https://github.com/llvm/circt)
- [Torch-MLIR](https://github.com/llvm/torch-mlir)
- [Polygeist](https://github.com/llvm/Polygeist)
- [Lighthouse](https://github.com/llvm/lighthouse)
- [EUDSL](https://github.com/llvm/eudsl)
- [mlir-tcp](https://github.com/llvm/mlir-tcp)
- [ClangIR archive](https://github.com/llvm/clangir)

## Backend比較

- [GCC internals: passes](https://gcc.gnu.org/onlinedocs/gccint/Passes.html)
- [GCC internals: RTL](https://gcc.gnu.org/onlinedocs/gccint/RTL.html)
- [GCC machine descriptions](https://gcc.gnu.org/onlinedocs/gccint/Machine-Desc.html)
- [Cranelift](https://cranelift.dev/)
- [Cranelift repository](https://github.com/bytecodealliance/wasmtime/tree/main/cranelift)
- [VeriISLE](https://github.com/bytecodealliance/wasmtime/tree/main/cranelift/isle/veri)
- [QBE](https://c9x.me/compile/)
- [QBE IL](https://c9x.me/compile/doc/il.html)
- [Binaryen](https://github.com/WebAssembly/binaryen)
- [Graal compiler](https://www.graalvm.org/latest/reference-manual/java/compiler/)
- [CompCert](https://compcert.org/)
- [CompCert manual](https://compcert.org/man/)
- [Alive2](https://github.com/AliveToolkit/alive2)
- [Csmith](https://github.com/csmith-project/csmith)
- [YARPGen](https://github.com/intel/yarpgen)
- [egg](https://egraphs-good.github.io/)
- [Souper archive](https://github.com/google/souper)

## 言語compiler/runtime一次資料

- [Go compiler introduction](https://go.dev/src/cmd/compile/README)
- [Rust compiler overview](https://rustc-dev-guide.rust-lang.org/overview.html)
- [Rust MIR](https://rustc-dev-guide.rust-lang.org/mir/index.html)
- [Rust MIR optimization](https://rustc-dev-guide.rust-lang.org/mir/optimizations.html)
- [Swift compiler architecture](https://www.swift.org/swift-compiler/)
- [Swift SIL](https://github.com/swiftlang/swift/blob/main/docs/SIL.rst)
- [Python bytecode/dis](https://docs.python.org/3/library/dis.html)
- [Python glossary: bytecode](https://docs.python.org/3/glossary.html#term-bytecode)
- [OCaml bytecode compilation](https://ocaml.org/manual/5.4/comp.html)
- [OCaml native compilation](https://ocaml.org/manual/native.html)
- [OCaml Flambda](https://ocaml.org/manual/flambda.html)
- [GHC backends](https://ghc.gitlab.haskell.org/ghc/doc/users_guide/codegens.html)
- [GHC compiler stage dumps](https://ghc.gitlab.haskell.org/ghc/doc/users_guide/debugging.html)
- [V8 Sparkplug](https://v8.dev/blog/sparkplug)
- [V8 Maglev](https://v8.dev/blog/maglev)
- [OpenJDK HotSpot compiler](https://openjdk.org/groups/hotspot/docs/HotSpotGlossary.html)
- [.NET tiered compilation](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/compilation)
- [Julia JIT design](https://docs.julialang.org/en/v1/devdocs/jit/)
- [Julia inference](https://docs.julialang.org/en/v1/devdocs/inference/)
- [Zig self-hosted x86 backend](https://ziglang.org/devlog/2025/)
- [WebAssembly core specification](https://webassembly.github.io/spec/core/)
- [Clojure evaluation/compiler behavior](https://clojure.org/reference/evaluation)

## Foundational papers/books to look up

以下は題名を示すbibliographyです。project ZIPへ著作物本文は同梱していません。

- Aho, Lam, Sethi, Ullman, *Compilers: Principles, Techniques, and Tools*.
- Muchnick, *Advanced Compiler Design and Implementation*.
- Appel, *Modern Compiler Implementation*.
- Cytron et al., *Efficiently Computing Static Single Assignment Form and the Control Dependence Graph*.
- Briggs et al., *Improvements to Graph Coloring Register Allocation*.
- Poletto and Sarkar, *Linear Scan Register Allocation*.
- Leroy, *Formal Verification of a Realistic Compiler*.
- Tate et al., *Equality Saturation: A New Approach to Optimization*.

## Interpretation cautions

- GitHub `open_issues_count`はpull requestも含む。
- repository size API field is repository storage metadataで、source line数ではない。
- LLVM `main` documentationは次期開発版を示し、stable manualとは一致しない場合がある。
- 各compilerのperformance claimはhardware、version、flags、corpusで変わる。本資料ではarchitectureの証拠として読み、Kofunの性能予測値には使わない。
- GHC、Zig、CPython等の現行pipelineは進化中であるため、実験時のversionを再確認する。
