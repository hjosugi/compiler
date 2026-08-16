# Changelog

このprojectは[Semantic Versioning](https://semver.org/)に従います。

## 1.1.0 - 2026-08-16

- RepositoryとPython distributionを`MIT`（SPDX）で明示し、標準本文をrelease artifactへ収録。
- CLIをphase-aware pipelineへ分割し、tokens/AST表示で不要な後段passを実行しない構造へ整理。
- KIR verifierへidentifier、i64 constant範囲、operation属性schemaのfail-closed検査を追加。
- 負のinteger literalを正規化し、signed i64最小値と境界外・negation overflowを正しく区別。
- LLVM emitterとreference interpreterが入力KIRをconsumer境界で再検証するよう堅牢化。
- Interpreter再実行時の出力状態、CLI出力directory、package metadataの回帰テストを追加。
- LLVM/reference differential corpusを正常系5programへ拡張。

## 1.0.1 - 2026-08-16

- GitHub ReleaseからZIPとchecksumを同じdirectoryへdownloadした直後に、`sha256sum -c`で検証できるようchecksum内のpathをbasenameへ修正。
- CIにrelease artifactのchecksum回帰テストを追加。

## 1.0.0 - 2026-08-16

- 5段階でlexer、parser、interpreter、type checker、bytecode VMを作るtutorialを統合。
- KofuMiniのtyped frontend、SSA KIR、verifier、reference interpreter、textual LLVM IR backendを収録。
- LLVM 22.1.8 / 23.1.0-rc3時点のLLVM Organization、CodeGen、関連project調査を固定。
- GCC、Cranelift、QBE、Binaryen、Graal、CompCertなどのbackend比較を収録。
- 言語史、IR/SSA、machine code、ABI/link/runtime、正しさ、benchmark、Kofun戦略を一続きの学習経路へ整理。
- dominance、instruction selection、linear scanとbenchmark protocolの実行可能labを収録。
- repository rootへpackage設定、test入口、GitHub Actions、release packagingを統合。
