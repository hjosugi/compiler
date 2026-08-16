# ABI・object・link・runtime

compilerが正しい命令を選んでも、ABIとlink/runtimeが誤ればprogramは動きません。

## ABIが決めるもの

- primitive/aggregateのsize、alignment、layout
- 引数、戻り値、hidden引数の渡し方
- caller/callee-saved registers
- stack alignment、red zone、shadow space
- symbol naming/visibility、TLS
- exception/unwind、debugとの契約

language ABIとC ABIを分けると、内部callはownershipやspecialized genericに最適化し、export boundaryだけ安定C ABIへlowerできます。公開ABIを変えると既存binary互換性へ影響するため、versioning方針が必要です。

## Object format

| Format | 主なplatform | 代表概念 |
|---|---|---|
| ELF | Linux/Unix系 | section、symbol table、REL/RELA、GOT/PLT |
| COFF/PE | Windows | section、import table、PDB ecosystem |
| Mach-O | Apple | load command、segment/section、dyld info |
| Wasm module | browser/WASI等 | typed section、import/export、validation |

objectは未解決symbolとrelocationを持てます。executable/shared libraryはlinkerが複数object/libraryを結合して作ります。

## Static linkerの仕事

1. input file/libraryを読む
2. symbolをresolveし、dead sectionを除去
3. sectionを配置してaddressを決める
4. relocationを適用する
5. branch rangeに応じてthunk/relaxationを行う
6. executable/shared object metadataを出す

LLDはLLVM projectのlinker群です。LTOではlinkerがbitcodeとnative objectを扱い、compiler optimizationとsymbol resolutionが接続します。

## Dynamic linking

shared libraryはdisk/memoryを共有しupdateしやすい一方、startup relocation、symbol interposition、version compatibilityが必要です。PICはload addressに依存しないcodeを作り、GOT/PLT等を介してdata/functionを参照します。security hardeningとしてPIE、RELRO、now binding等があります。

## Runtime support

言語機能はhidden runtime contractを持ちます。

| Feature | compilerが出すもの | runtime側 |
|---|---|---|
| checked arithmetic | overflow branch/trap | trap handler optional |
| GC | safepoint、stack map、barrier | allocator、collector、thread coordination |
| exception | landing pad、unwind table | personality、unwinder |
| async | state machine、resume function | scheduler、waker、I/O reactor |
| closure | environment layout、call shim | allocator/lifetime policy |
| thread-local | TLS access model/relocation | loader/thread runtime |
| sanitizer | instrumentation call | sanitizer runtime |

KofuMiniは`printf`と`llvm.trap`だけに依存します。本格Kofun v0はpanic=abort、GCなし、exception unwindなしでruntime surfaceを意図的に小さくします。

## Debugとunwind

DWARF/PDB等はsource file、line、scope、variable location、typeをmachine addressへ対応させます。optimizationにより値が消える・移動する・複数箇所に分かれるため、debug infoもpassで更新します。unwind情報はdebuggerだけでなくexception、profiler、crash reportingに必要です。

## 最初のdirect ELF writer

段階を分けます。

1. assembly text出力 + system assembler/linker
2. `.text`のみのELF relocatableとlocal symbol
3. function/data section、symbol table、relocation
4. debug line、unwind
5. PIC/shared library
6. direct executable imageは最後

object writerを早く作りすぎるとbackendの価値よりformat作業が支配します。correctness oracleを保つため、各段階のobjectを`readelf`/`objdump`/LLDで検査します。

