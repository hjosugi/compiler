# LLVM Organization完全整理

## Snapshot

調査日: 2026-08-16

公開GitHub APIから確認できたLLVM Organizationのrepositoryは44件です。中心の[`llvm/llvm-project`](https://github.com/llvm/llvm-project)は次の規模でした。

| 項目 | Snapshot |
|---|---:|
| Stars | 39,815 |
| Forks | 18,249 |
| Repository size field | 4,266,454 KB |
| Open issues count field | 38,205 |
| Default branch | `main` |

GitHubの`open_issues_count`はpull requestも含むため、純粋なbug件数ではありません。数値はprojectの品質を表すscoreではなく、規模を理解するためのsnapshotです。

全44 repositoryの分類は[`data/llvm_org_repositories_2026-08-16.tsv`](../data/llvm_org_repositories_2026-08-16.tsv)、API queryと取得時刻は[`snapshot-manifest.json`](../data/snapshot-manifest.json)に収録しています。

## 1. `llvm-project`は何か

`llvm-project`はLLVM IR/backendだけのrepositoryではありません。主要subprojectを1つのmonorepoで管理しています。

### CompilerとIR

- `llvm/`: LLVM IR、analysis、optimization、CodeGen、target、MC、tools
- `clang/`: C-family frontend
- `mlir/`: multi-level IRとdialect framework
- `flang/`: Fortran frontend
- `polly/`: polyhedral optimization
- `bolt/`: linked binaryに対するpost-link optimization

### Toolchain

- `lld/`: ELF、COFF、Mach-O、WebAssembly linker
- `lldb/`: debugger
- `clang-tools-extra/`: clangd、clang-tidyなど
- `orc-rt/`: ORC JIT runtime

### Runtimeとlibrary

- `compiler-rt/`: sanitizer、profile、builtins
- `libc/`: C library
- `libcxx/`: C++ standard library
- `libcxxabi/`: C++ ABI
- `libunwind/`: stack unwinding
- `openmp/`: OpenMP
- `offload/`, `libclc/`, `libsycl/`: accelerator/offload領域

Monorepo component一覧は[`data/llvm_project_components_2026-08-16.tsv`](../data/llvm_project_components_2026-08-16.tsv)に固定しています。

## 2. LLVM core内部

調査時点の`llvm/lib`では、backendに直結する部分だけでも次の規模です。

- `llvm/lib/CodeGen`: 258 top-level entries
- `llvm/lib/Target`: 32 entries、うち約27 target directory
- `llvm/lib/Analysis`: 126 top-level entries
- `llvm/lib/Transforms`: 12 category entries

Target directoryにはAArch64、AMDGPU、ARM、AVR、BPF、DirectX、LoongArch、Mips、NVPTX、PowerPC、RISCV、SPIR-V、SystemZ、WebAssembly、X86などがあります。すべてが同じ成熟度・support tierではありません。

ここから分かるのは、LLVMを超える対象が単一algorithmではないことです。Instruction selectorだけでもSelectionDAG、FastISel、GlobalISelがあり、その前後にlegalization、register-bank selection、Machine IR pass、register allocation、scheduling、MC emissionがあります。

## 3. MLIR関連repository

LLVM Organizationの現在の拡張中心はMLIR ecosystemです。

| Repository | 役割 | Kofunへの示唆 |
|---|---|---|
| `mlir/` | Dialect、conversion、pass、execution | 複数levelのIRを保つ設計 |
| `circt` | Hardware designをMLIRで扱う | domain-specific IRの成功例 |
| `torch-mlir` | PyTorch/ONNXからMLIRへ | frontend重複を減らすingress |
| `Polygeist` | C/C++を高いMLIRへraise | 低level化しすぎたIRを戻す研究 |
| `lighthouse` | ingress→schedule→runtimeのreference | pipelineを実行可能な形で共有 |
| `eudsl` | Python/DSL/TableGen tooling | compiler構築APIの使いやすさ |
| `mlir-tcp` | Tensor Compute Primitives | ML中間表現の共通化 |
| `clangir` | 旧incubator | ClangIR本体統合後にarchive |

MLIRの重要な教訓は、「万能な1つのLow IRへすぐ落とさない」ことです。高level構造、loop、tensor、ownershipなどを表現できるIRを保ち、段階的にlowerします。

KofunもMLIRそのものを導入する必要はありませんが、KIR-H、KIR-M、MIRの複数levelを持つ設計は採用価値があります。

## 4. Quality ecosystem

LLVMの強さを支えるrepository:

- `llvm-test-suite`: compile/runtime benchmark corpus
- `llvm-lnt`: 長期performance trendの収集と可視化
- `llvm-zorg`: Buildbotと継続的platform testing
- `bolt-test-suite`: post-link optimizer専用corpus
- `offload-test-suite`: accelerator/offload testing
- `cross-project-tests`: monorepo内integration

LLVMと競う場合、optimization数だけ増やしても不十分です。Regressionを検出・bisect・再現できる測定基盤がbackendと同じ重要度を持ちます。

## 5. Release ecosystem

2026-08-16時点:

- 安定版: LLVM 22.1.8
- 次期release: LLVM 23.1.0-rc3
- `main`のdocumentation: LLVM 24.0.0git向けであり、安定版manualではない

LLVM公式documentationの`ReleaseNotes`は常に次期開発版を指す場合があります。実験結果には必ずtag、commit、target triple、CPU、flagsを記録します。

## 6. LLVM Organizationから学ぶべき構造

1. **Coreとecosystemを分ける**: compiler本体、runtime、test、releaseを別責務にする
2. **IRを公開contractにする**: frontendとbackendを組み合わせられるようにする
3. **Target descriptionをdata化する**: TableGenのようにinstruction定義からboilerplateを生成する
4. **Benchmarkを継続運用する**: 一度の勝利ではなくregressionを追う
5. **Optional projectを許す**: CIRCTやTorch-MLIRのようにcore以外で実験する
6. **Integration gateを持つ**: subproject単体成功とtoolchain全体成功を区別する

## 7. そのまま真似しない部分

以下は規模からの推論です。

- 数十targetの抽象化はKofun初期backendには過剰
- 旧/new pass managerの併存のような長期migration costを避ける
- SelectionDAG/FastISel/GlobalISelを同時に持たず、baselineとoptimizingの2 pipelineに限定する
- 巨大C++ APIを埋め込まず、安定したKIR schemaとprocess-independent artifactsを優先する
- source semanticsをLLVM IR属性へ早期変換しない

Kofunは最初にx86-64 LinuxとAArch64 Linuxへ限定し、determinism、compile speed、correctnessを深く追う方が勝ち筋があります。
