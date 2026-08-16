# IR・SSA・最適化

## なぜ複数IRか

sourceに近いほど型、ownership、effect、generic、source位置が豊富です。machineに近いほどregister class、instruction latency、ABIが重要です。1つのIRへ全部を詰めると、passが不要な複雑性を背負います。

| Level | 保持する情報 | 代表変換 |
|---|---|---|
| HIR | 名前解決済みsyntax、型、effect | desugar、generic/effect解析 |
| semantic MIR | CFG、ownership、drop、checked op | borrow/definite-init、specialization |
| optimizer SSA | value/memory dependency | SCCP、GVN、LICM、inlining |
| generic machine IR | legalizing前のmachine op | legalization、instruction selection |
| target MIR | register class、ABI、encoding候補 | regalloc、schedule、peephole |

## CFG、dominance、SSA

basic blockは途中にbranchがなく末尾だけがterminatorです。AがBをdominateするとは、entryからBへの全pathがAを通ることです。定義は全使用をdominateする必要があります。分岐で別々に定義された値は合流点で`phi`により統合します。

```text
entry: branch %cond, then, else
then:  %a = ...; jump merge
else:  %b = ...; jump merge
merge: %x = phi [%a, then], [%b, else]
```

`labs/dominators.py`でiterative dominator algorithmを実行できます。mutable localをSSA化する本格実装ではdominance frontierにphiを配置し、dominator tree上でrenameします。

## MemoryはSSA値ほど単純ではない

`load p`と`store q`の順を変えられるかは`p`と`q`がaliasするかに依存します。

- basic AA: type、offset、object identityなどで推論
- function attributes: readonly、noalias、nocapture等
- MemorySSA: memory definition/useのversion関係を表す
- ownership IR: unique borrowならfrontend由来のnoalias factを保持可能

誤ったalias metadataは速いmiscompileを作るため、証明できるfactだけ付けます。

## Data-flow framework

各blockにfact集合を持ち、predecessor/successorからmeetし、transfer functionをfixed pointまで反復します。

| Analysis | 方向 | lattice/fact例 |
|---|---|---|
| reaching definitions | forward | 到達する定義集合 |
| liveness | backward | 後で使われる値集合 |
| constant propagation | forward | unknown / constant / overdefined |
| definite initialization | forward | 初期化済み変数集合 |

worklistで変更のあった隣接blockだけ再計算します。loopがあっても有限height latticeなら収束します。

## 主要optimizationを安全条件で考える

| 変換 | 例 | 必要条件 |
|---|---|---|
| constant folding | `2*3→6` | source overflow/FP semanticsを維持 |
| DCE | unused pure opを削除 | trap/volatile/IOでない |
| CSE/GVN | 同じ式を共有 | operand、memory version、flagsが同値 |
| LICM | loop invariantを外へ | dominates exits、speculation安全、aliasなし |
| inlining | call bodyを展開 | ABI/semantics維持、size budget |
| SROA | aggregateをscalar化 | observable layout/addressを壊さない |
| vectorization | scalar loop→SIMD | dependence、alignment、remainder処理 |
| strength reduction | multiply→shift/add | signed/overflow costと意味が同じ |

passは入力condition、出力invariant、preserveするanalysis、cost budget、検証法を文書化します。

## KIRとの対応

KofuMini KIRは学習用のtyped SSAです。immutable `let`なのでphi挿入algorithmなしでもexpression lowering時にSSAを構築できます。`if`と短絡logicはCFG+phiへlowerします。次の拡張順は:

1. use-def/type verifier
2. predecessor/phi verifier
3. constant foldingとDCE
4. mutable localをstack slotで表現
5. mem2regでSSA化
6. loopとdominance frontier
7. ownership/alias facts

各pass前後にKIR interpreterを実行し、結果とtrap behaviorが同じことを確認します。

