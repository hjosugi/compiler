# KIR v1設計ノート — 意味論、直列化、hash規約

## Status

これはCompiler Atlasの設計教材であり、KofunでacceptされたRFCではありません。将来のRFC-0019候補を議論できる粒度へ分解したものです。Kofunのauthoritativeな現状は、2026-08-16 snapshotの[`COMPILER_ARCHITECTURE.md`](https://github.com/kofun-lang/kofun/blob/075fbb241367c27863c74f3884989ba7ddbbfa5b/docs/COMPILER_ARCHITECTURE.md)と[`RFC-0018/A01`](https://github.com/kofun-lang/kofun/blob/075fbb241367c27863c74f3884989ba7ddbbfa5b/rfcs/0018-self-contained-native-toolchain.md)です。

現在のC11、direct native、wasm32は同じgeneral frontend / typed IRを共有せず、それぞれ別のbounded Coreを解析します。したがってLLVMを先に追加すると、4本目のfrontendを増やす危険があります。先に固定するcontractは次です。

```text
Kofun source
  -> lexer / parser / name resolution
  -> type / ownership / effect checking
  -> KIR-H: source semantics and capabilities
  -> KIR-M: target-independent CFG and typed SSA
  -> backend boundary
       +-> C11 bootstrap
       +-> direct native
       +-> wasm32
       `-> llvm-hosted (optional)
```

KofuMiniはこのうち`KIR-M`の非常に小さい実行例です。ownership、memory、generic、module ABIを実装していないため、そのままKofun KIRにはなりません。

## 1. 意味論

### 1.1 KIRを「小さいLLVM IR」にしない

LLVM IRへ早く落とすと、sourceで証明済みだった情報が一般的なpointer/memory operationへ潰れます。KIR-Hには少なくとも次をfirst-classに残します。

- `read` / `edit` / `take`とresource state transition
- unique、shared、escapedなどのalias factと、そのproof origin
- authority / effect set、`pure`、`noalloc`、`nothrow`
- checked、wrapping、saturatingを区別したnumeric operation
- ADT constructor、exhaustive match、unreachable proof
- generic definition identity、specialization key、dictionary identity
- cleanup / drop obligationと正常・trap edge
- separate compilation用のpublic ABI / layout identity
- tail positionと、必須tail callかoptimization hintかの区別

これらは単なるoptimization hintではありません。source semanticsに属するfactと、backendが無視できるadvisory metadataをschema上で分けます。正しさに必要なfieldを未知backendが捨てる場合、そのbackendはartifact生成を拒否します。

### 1.2 KIR-Mの最小operation contract

KofuMiniのimplemented subsetは次です。

| Group | Operation | Semantics |
|---|---|---|
| constant | `const` | `Int`または`Bool`のtyped value |
| arithmetic | `iadd/isub/imul.checked` | signed i64。overflowはtrap |
| division | `idiv/irem.checked` | 0除算と`INT64_MIN / -1`はtrap、0方向へ丸める |
| comparison | `icmp.*` | operand typeを明示し`Bool`を返す |
| control | `branch`, `jump`, `phi`, `return` | CFG edgeとSSA valueを明示 |
| call | `call` | callee signatureとargument typeが一致 |
| effect | `print.i64` | observable stdout effect。DCE禁止 |

KIR verifierは、known type/op、terminator、到達可能性、SSA一意性、use-before-def、dominance、call signature、`phi` predecessor集合、return typeを検査します。不正KIRをLLVMへ渡してerrorの責任を後段へ移しません。

### 1.3 Trap、undefined behavior、poison

Kofunのobservable semanticsをLLVMのundefined behaviorへ暗黙変換しません。

- checked overflowはLLVM overflow intrinsicのflagを検査して明示trapする。
- 0除算をLLVM `sdiv`へ無条件に渡さない。
- 証明のない`nsw`、`nuw`、`inbounds`、`noalias`を付けない。
- unreachable proofがないsource pathをLLVM `unreachable`へ変換しない。

Backend固有loweringは、このcontractと同値であることをreference interpreterまたはtranslation validatorで確認します。

### 1.4 Ownership / alias fact

Alias factは`metadata: string`ではなく、scopeと失効条件を持つtyped recordにします。

```text
AliasFact {
  subject: ValueId,
  kind: unique | shared_read | escaped | unknown,
  proof: ownership_check | region_check | call_contract,
  valid_from: OperationId,
  valid_until: OperationId | function_exit
}
```

`edit`中のunique factは、unknown foreign call、pointer escape、shared conversionなどで失効します。backendが`noalias`へ写すのは、対象scope全体でfactが有効な場合だけです。Verifierはproof identityと失効edgeを検査し、optimization passはfactを新しく発明せず、保持・弱化・消費のいずれかを記録します。

### 1.5 Tail call

「tail position」と「必ずconstant stackで実行する」は別contractです。

- `tail`: backendが通常callへ落としてもprogram semanticsは同じで、性能だけが変わる。
- `musttail`: ABI-compatibleなtail jumpを生成できなければcompile error。silent fallback禁止。

KIR v1で`musttail`を持つなら、callee/caller calling convention、return representation、ownership cleanup、authority lifetimeが一致することをfrontendまたはverifierで証明します。

## 2. 直列化形式

### 2.1 目的

直列化はdebug dumpだけでなく、separate compilation、cache、reproducer、differential testのcontractです。次を同時に満たします。

- 同じsemantic inputからbyte-identical output
- schema versionを必須化し、unknown required fieldを拒否
- human-readableなcanonical text/JSONと、将来のcompact binaryを同じdata modelから生成
- source path、wall clock、hash-map iteration orderをsemantic bytesへ混入させない
- diagnostic/source mapをsemantic payloadと分離して結合可能にする

### 2.2 KofuMiniで動かす

KofuMiniはcanonical JSON `kofumini.kir/v1`を実装しています。

```bash
export PYTHONPATH="$PWD/src"
python3 -m kofumini.cli kir-json examples/kofumini/choose.kofu
python3 -m kofumini.cli kir-hash examples/kofumini/choose.kofu
```

規約はUTF-8、JSON keyのlexicographic sort、余分な空白なし、function/block/instructionのsemantic order保持です。Map orderやPython processには依存しません。

### 2.3 Proposed Kofun envelope

```text
KIRArtifact {
  schema: "kofun.kir/v1",
  language_contract: Digest,
  producer: { compiler_digest, frontend_profile },
  imports: [InterfaceDigest...],
  types: [CanonicalType...],
  functions: [CanonicalFunction...],
  exports: [Export...],
  semantic_digest: Digest,
  diagnostics_digest?: Digest
}
```

Target triple、CPU feature、optimization profileはKIR自体を変えるparameterなのか、backend cache keyだけなのかをfieldごとに決めます。Target-independent KIRへhost filesystem pathやinstalled toolの有無を入れません。

### 2.4 Versioning

- Major schema change: readerが意味を保てない。明示migrationまたは拒否。
- Optional field: default semanticsをschemaに固定し、unknownでも安全なものだけ。
- Required capability: `required_features`へ列挙し、未対応consumerはartifact全体を拒否。
- Canonicalization change: hash namespaceもversion upし、旧cacheと混ぜない。

## 3. Hash規約

### 3.1 二つのhash

KofuMiniは実行可能な縮小例として次を持ちます。

- module content hash: canonical module bytesのSHA-256
- function content hash: `kofumini.kir-function/v1` envelope + canonical functionのSHA-256

Function hashはsource textの空白やfile pathではなく、lower済みsemantic contentに結び付きます。実装は[`src/kofumini/kir.py`](../src/kofumini/kir.py)です。

### 3.2 Kofun function identityに含めるもの

- canonical function signature、calling convention、effect/authority contract
- canonical type/layout identity
- normalized CFG、operation、operand、required attribute
- ownership/alias factとcleanup obligation
- generic strategyとconcrete specialization/dictionary identity
- direct calleeのinterface/ABI digest
- language semanticsとKIR schema version

次はsemantic function hashから除外し、別のdiagnostic/reproducer identityへ入れます。

- absolute source path
- timestamp、hostname、process id
- comment、formatting
- diagnostic colorや表示幅
- profileに影響しないsource location

Source locationがpanic stack、reflection、coverageなどobservable behaviorへ影響するprofileでは、normalized location digestをsemantic inputとして明示します。

### 3.3 Cache key

Backend cacheはfunction hashだけでは足りません。

```text
BackendKey = H(
  function_semantic_hash,
  target_triple,
  cpu_features,
  code_model,
  optimization_profile,
  runtime_abi_digest,
  backend_implementation_digest
)
```

Object/image layoutはsymbol orderやsection alignmentにも依存するため、link/image cacheはexport graphとlayout policyを追加します。Digest mismatchでは再利用せず、古いartifactへfallbackしません。

### 3.4 決定論gate

同じinputを少なくとも次の変化下で複数回buildし、KIR、object/image、diagnosticを対象別に比較します。

- process再起動
- parallel job数
- clean directoryのabsolute path
- hash randomization
- locale/timezone
- declaration discovery order

差が許されるfieldはnormalize ruleと理由をschemaに書きます。「比較前に全部消す」normalizerは不正なnondeterminismを隠すため禁止します。

## Backend導入順

Big-bang移行は行いません。

1. General parser、name resolution、type/ownership/effect checkerを一つにする。
2. KIR v1 semantics、serialization、hash、verifierをgateする。
3. C11を最初のconsumerにし、旧C11経路とdifferential testする。
4. Direct nativeとwasm32を一つずつKIR consumerへ移す。旧経路は比較oracleとして残す。
5. `llvm-hosted-*`をtextual `.ll` emitterとして追加する。
6. 全backendのstdout、exit/trap、artifact identityを比較する。

LLVM targetのcontract:

- LLVM未導入時は`llvm-hosted`だけを明示拒否。
- Direct targetからLLVMへのsilent fallback禁止。
- KIRより前のfrontendを複製しない。
- Source semanticsをLLVM metadataやUBへ委譲しない。
- LLVM version、target triple、CPU、flagsをbenchmark artifactへ保存。

RFC-0018はLLVMをpermanent hostとしてrejectしますが、bootstrapまたはoptional backend experimentは許容しています。この構成ならself-contained direct pathと比較用LLVM pathを混同しません。

## Completion gate

KIR v1を「完成」と呼べる最小条件:

- semantics、serialization、hash namespaceがversioned documentとmachine-readable schemaで一致
- verifierにnormal、boundary、malformed、dominance、type、ownership negative test
- same frontend resultからC11/referenceのdifferential corpusが一致
- function order、parallelism、pathを変えてcanonical bytesが一致
- one-function editで無関係function hashが変わらない
- required featureを知らないbackendがfail closed
- LLVM/direct/wasmのbackend identityがartifact manifestに現れ、fallback testがある

このgateが先です。Instruction selectionやregister allocationを外部backendへ任せても、ここに挙げたsource semantics、ABI、separate compilation、determinismの問題は残ります。
