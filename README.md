# Compiler Atlas

[![CI](https://github.com/hjosugi/compiler/actions/workflows/ci.yml/badge.svg)](https://github.com/hjosugi/compiler/actions/workflows/ci.yml)

Compilerと言語処理系をゼロから作り、typed SSA IRからLLVM IR、native executableまで到達する日本語の実行可能教材です。LLVM内部、主要backend、machine code、ABI/link/runtime、検証、benchmark、言語史、Kofun向けbackend戦略を一つのrepositoryに統合しています。

調査snapshotは**2026-08-16**です。公式releaseで安定版だったLLVM **22.1.8**を再現基準とし、LLVM **23.1.0-rc3**はprereleaseとして区別しています。時点依存情報は[`toolchain.lock.json`](toolchain.lock.json)と[`data/`](data/)へ固定しています。

## まず動かす

必須なのはPython 3.11以上だけです。

```bash
git clone https://github.com/hjosugi/compiler.git
cd compiler
make check-python
make demo
```

Clang、`llvm-as`、`opt`がある環境ではLLVM/native経路まで検証できます。

```bash
make check-llvm
make native
make benchmark-smoke
```

## 一つの学習経路

| 順序 | 内容 | 実行物・資料 |
|---:|---|---|
| 1 | 電卓から関数・型検査・bytecode VMまで5段で作る | [`tutorial/`](tutorial/) |
| 2 | 完成した小型typed compilerを一周する | [KofuMini walkthrough](docs/00-from-zero.md) |
| 3 | frontend、複数IR、backend、runtimeの責務を分ける | [Compiler pipeline](docs/01-compiler-pipeline.md) |
| 4 | LLVM Organizationと関連projectを把握する | [LLVM Organization](docs/02-llvm-organization.md) |
| 5 | LLVM CodeGenをIRからMC/objectまで追う | [LLVM backend](docs/03-llvm-backend.md) |
| 6 | LLVM以外のbackendと選択基準を比較する | [Backend landscape](docs/04-backend-landscape.md) |
| 7 | SSA、dominance、optimizationを実装する | [IR / SSA](docs/05-ir-ssa-optimization.md)、[`labs/`](labs/) |
| 8 | ABI、object、linker、runtimeまで理解する | [Machine code](docs/06-machine-code-generation.md)、[ABI/link/runtime](docs/07-abi-link-runtime.md) |
| 9 | miscompileを検出し、性能を再現可能に測る | [Correctness](docs/08-correctness-and-benchmarking.md)、[`benchmarks/`](benchmarks/) |
| 10 | 歴史と他言語の設計判断を自分の言語へ戻す | [言語史・設計atlas](docs/12-language-history-design-atlas.md) |
| 11 | Kofunのshared KIRとoptional LLVM backendを設計する | [Kofun strategy](docs/09-kofun-beyond-llvm.md)、[KIR v1](docs/14-kir-v1-design.md) |

短時間で全体を選ぶ場合は[学習マップ](docs/00-learning-map.md)、手を動かす課題は[段階演習](docs/13-exercises.md)、用語確認は[用語集](docs/11-glossary.md)から始めてください。

Kofun側へ渡す作業分解は[12件のlocal Issue pack](docs/15-kofun-kir-issue-pack.md)にあります。これはplanning artifactであり、このrepositoryからKofunのremote Issueを作成しません。

## 実装されているcompiler

KofuMiniはPython標準libraryだけで動く小型typed languageです。

```text
.kofu source
  -> Lexer
  -> Parser / AST
  -> Type checker
  -> typed SSA KIR
  -> KIR verifier
  +-> KIR reference interpreter
  `-> textual LLVM IR
       -> Clang / LLVM optimizer and CodeGen
       -> native executable
```

```bash
export PYTHONPATH="$PWD/src"
python3 -m kofumini.cli tokens examples/kofumini/choose.kofu
python3 -m kofumini.cli ast    examples/kofumini/choose.kofu
python3 -m kofumini.cli check  examples/kofumini/choose.kofu
python3 -m kofumini.cli kir    examples/kofumini/choose.kofu
python3 -m kofumini.cli llvm   examples/kofumini/choose.kofu
python3 -m kofumini.cli run    examples/kofumini/choose.kofu
python3 -m kofumini.cli build  examples/kofumini/choose.kofu -O2 -o build/choose
```

KofuMiniは`Int`、`Bool`、immutable `let`、関数、値を返す`if`、短絡論理、checked arithmetic、`print`を実装します。配列、heap、module、generic、ownership、exception、debug informationは意図的に未実装です。これはproduction compilerではなく、各層の契約を観察できるreference implementationです。

`tutorial/`のMiniとKofuMiniは目的の違う二つの小型dialectです。前者は各stageの差分を小さくするため型注釈のない文中心の構文、後者はtyped SSAとLLVM loweringを明示する型付き・式中心の構文です。同一言語であるという誤った主張はしません。

## Repository構成

| Path | 内容 |
|---|---|
| [`tutorial/`](tutorial/) | 単体で動く5段階の言語処理系と`.mini`例 |
| [`src/kofumini/`](src/kofumini/) | typed frontend、SSA KIR、interpreter、LLVM emitter、CLI |
| [`examples/kofumini/`](examples/kofumini/) | 正常系、型error、overflow、短絡評価の`.kofu`例 |
| [`tests/`](tests/) | frontend、KIR、LLVM/native、tutorial、lab、docsのtest |
| [`docs/`](docs/) | compiler全体、LLVM、他backend、言語史、Kofun戦略、出典 |
| [`labs/`](labs/) | dominance、instruction selection、linear scanの最小実装 |
| [`benchmarks/`](benchmarks/) | correctness-firstの比較runnerとJSON schema |
| [`data/`](data/) | 取得日・API queryを固定したLLVM Organization/component snapshot |
| [`scripts/`](scripts/) | check、demo、文書整合、release ZIP生成 |

## LLVMの位置付け

LLVMは型検査、ownership、effect、generic strategy、言語ABIそのものを決めません。Kofunで先に必要なのはgeneral frontendとbackend非依存のshared typed KIRです。その後にLLVMを次の用途で薄く接続します。

- 自前backendのmiscompileを発見するdifferential-testing oracle
- compile time、runtime、binary sizeを比較する対照系
- 未対応targetやdebug情報のoptional escape hatch

このprojectのKofuMiniも、C++ APIやlibLLVM bindingを持たず、KIRからtextual `.ll`を生成します。LLVMがない環境ではreference interpreterを使え、LLVMへのsilent fallbackはありません。direct native backendはroadmapとlabの対象であり、完成済みとは表示しません。

## 検証方針

`make check`は次を一つの入口で検査します。

- Python sourceのcompile確認
- frontend、型検査、KIR lowering、reference interpreter
- KIR/LLVMの構造とerror path
- tutorial各stageのsemantic一致とscope/zero-argument call境界
- dominance、instruction selection、linear scan
- benchmark helperとJSON contract
- Markdownのlocal linkと旧directory参照
- 利用可能なら`llvm-as`、`opt`、Clang nativeとのdifferential test

CIではPython 3.11/3.14のpure-Python gateと、LLVM toolchainを導入するnative gateを分離します。skipは成功に偽装せず、`make check-llvm`ではtool不足をfailureにします。

## 調査範囲と限界

LLVM Organizationの全repository snapshotと`llvm-project`主要componentを収録します。一方、「歴史上存在した全言語」「全CPU」「LLVMの全source file」を有限の教材で完全列挙することはできません。言語史は設計上の分岐を生んだ代表familyを選び、backend調査は一次資料へ辿れる分類と再現可能なsnapshotを重視します。

資料・コードの誤りはissueで再現例と一次資料を添えて報告してください。外部linkは変化し得るため、事実を再利用するときは[`SOURCES.md`](docs/SOURCES.md)とsnapshot日を確認してください。

## Release

`make package VERSION=v1.0.0`はtracked treeから決定的な名前のZIPとSHA-256 fileを`dist/`へ生成し、CRCを検査します。GitHub ReleaseにはこのZIPとchecksumを添付します。

## License

このrepositoryには現時点で再利用licenseを設定していません。公開閲覧できること自体は、copy・改変・再配布の許諾を意味しません。
