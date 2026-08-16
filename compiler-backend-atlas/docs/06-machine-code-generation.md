# Machine code生成

この章はgeneric SSAからCPU命令列までの判断を分解します。教材は`labs/instruction_selection.py`と`labs/linear_scan.py`に対応します。

## 1. Legalization

IRの型/演算がtargetに直接存在するとは限りません。

- 32-bit targetの`i64`をpairへ分解
- unsupported vector幅をsplit/scalarize
- 小さい整数をpromoteし、結果をtruncate
- integer divisionをinstructionまたはruntime callへlower
- atomicをtarget instruction sequenceまたはlibcallへlower

legalization ruleは`legal`、`widen`、`narrow`、`lower`、`libcall`等を選び、必ず停止するmeasureを持たせます。

## 2. Instruction selection

同じIR式にも複数のcoverがあります。`a + b*4`はx86 addressing mode `a + b*4`としてloadに吸収できる場合があります。selectorはpatternが一致するかだけでなく、latency、size、register pressure、fold可能性をcostにします。

代表方式:

- tree/DAG pattern matching
- bottom-up rewriteとdynamic programming
- graph covering
- equality saturationで候補を保持し後でextract
- superoptimizerで局所列を探索

`labs/instruction_selection.py`はtree coverの最小例です。本格実装ではside effect、flags、multi-result、memory ordering、DAG shared nodeを扱います。

## 3. Calling convention lowering

関数引数/戻り値をregister/stackへ割り当て、call-clobbered register、stack alignment、variadic、aggregate returnを決めます。x86-64でもSystem VとWindowsで規則が違います。IR function typeが同じでもABI sequenceは同じとは限りません。

## 4. Livenessとregister allocation

あるprogram pointより後で値が使われるならliveです。同時にliveな値は同じphysical registerを共有できません。

linear scanの流れ:

1. block orderを決める
2. use/defからlive intervalを作る
3. start順にintervalを走査
4. 終了済みactiveをexpire
5. 空registerを割当、なければspill候補を選ぶ

production品質にはholeのあるinterval、live range splitting、coalescing、precolored value、subregister、rematerialization、spill weight、loop depthが必要です。

## 5. Stack frame

frameにはspill slot、local object、callee-saved register、outgoing argument、alignment padding等があります。prologue/epilogueはstack pointerを調整し、必要なregisterを保存復元します。frame pointer省略、red zone、stack probe、canary、shadow call stackはplatform/security policyです。

## 6. Scheduling

dependency DAGでdata、memory、control、flag dependencyを表し、ready instructionから選びます。

- latency最小化
- instruction-level parallelism
- register pressure抑制
- code size
- macro/micro fusion
- pipeline hazard回避

microarchitectureごとにcostが違うため、ISA名だけでなくCPU feature/modelを入力にします。

## 7. Encodingとrelocation

selected opcodeとoperandからbyte列を作ります。即値範囲、ModR/M・SIB、prefix、endianness、compressed instructionなどtarget固有規則を持ちます。address未確定ならfixup/relocationを生成します。

最初の自作backendは次に限定すると進みます。

| 項目 | v0 |
|---|---|
| target | x86-64 System V Linux |
| input | integer/Bool KIR subset |
| output | assembly text、次にELF relocatable |
| allocation | linear scan、caller-saved中心 |
| optimization | constant fold、local combine |
| debug | source line tableは後続phase |

まずassembly textをsystem assemblerへ渡してcorrectnessを確立し、その後encoder/object writerを自作します。一度にISA、ABI、ELFをdebugしないためです。

## 8. Target追加checklist

- data layout、endianness、pointer size
- integer/FP/vector legal types
- registers、classes、aliases、reserved registers
- instruction encodingとfeatures
- calling convention、varargs、aggregate rules
- frame、red zone、stack probe、unwind
- atomicsとmemory model
- TLS、PIC、relocations、object format
- assembler/disassembler round-trip
- debug register numbering
- conformance、differential、random tests

