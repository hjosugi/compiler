# Changelog

このprojectは[Semantic Versioning](https://semver.org/)に従います。

## 1.0.0 - 2026-08-16

- 5段階でlexer、parser、interpreter、type checker、bytecode VMを作るtutorialを統合。
- KofuMiniのtyped frontend、SSA KIR、verifier、reference interpreter、textual LLVM IR backendを収録。
- LLVM 22.1.8 / 23.1.0-rc3時点のLLVM Organization、CodeGen、関連project調査を固定。
- GCC、Cranelift、QBE、Binaryen、Graal、CompCertなどのbackend比較を収録。
- 言語史、IR/SSA、machine code、ABI/link/runtime、正しさ、benchmark、Kofun戦略を一続きの学習経路へ整理。
- dominance、instruction selection、linear scanとbenchmark protocolの実行可能labを収録。
- repository rootへpackage設定、test入口、GitHub Actions、release packagingを統合。
