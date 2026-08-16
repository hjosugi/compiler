# 用語集

| 用語 | 意味 |
|---|---|
| ABI | binary間のlayout、calling convention、symbol等の契約 |
| AST | source syntaxを木で表した構造 |
| AOT | 実行前にmachine codeを作る方式 |
| basic block | 途中分岐がなく末尾にterminatorを持つ命令列 |
| CFG | basic blockと制御遷移edgeのgraph |
| codegen | IRからmachine code/objectを生成する工程 |
| dominance | entryからBへの全pathがAを通る関係 |
| frontend | parse、name/type analysisなどsource寄り部分 |
| IR | compiler内部の中間表現 |
| instruction selection | generic operationをtarget instructionへ写す工程 |
| JIT | 実行中にmachine codeを生成する方式 |
| legalization | target未対応の型/演算を対応形へ変える工程 |
| linker | object/libraryのsymbol/relocationを解決し最終binaryを作るtool |
| liveness | 値が将来使われるprogram pointの解析 |
| lowering | 高水準表現をより低水準な表現へ変換すること |
| MIR | machine寄り、または言語のmid-level IR。文脈で異なる |
| object file | section、symbol、relocationを持つlink前のbinary |
| pass | IRを解析または変換するcompiler処理単位 |
| phi | CFG predecessorに応じてSSA値を選ぶoperation |
| PGO | 実行profileを使う最適化 |
| poison | LLVMで不正条件から生じ、使用によりUBへ伝播し得る値 |
| register allocation | virtual valueをphysical register/stackへ配置する工程 |
| relocation | link/load時にaddress等を補正する記録 |
| runtime | GC、scheduler、panic、reflection等を実行時に支えるcode |
| SSA | 各値を一度だけ定義するIR形式 |
| stack map | machine locationとGC/deopt上のlogical valueの対応 |
| TableGen | LLVMのtarget記述等からtables/codeを生成するDSL/tool |
| terminator | return/branchなどbasic block末尾の命令 |
| translation validation | 個々の変換結果が入力と同値か後から検証する方式 |
| UB | 仕様が動作を保証しないundefined behavior |
| verifier | IRの構造・型・不変条件を検査する処理 |

