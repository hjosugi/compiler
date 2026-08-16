# ゼロから言語とcompilerを作る

この章は「compilerの部品名はまだ知らない」という地点から、KofuMiniのsource codeが実行ファイルになるまでを追います。最初はPythonだけで動かし、最後にClang/LLVMを接続します。

## 0. 先に完成形を一度動かす

repository rootで次を実行します。

```bash
export PYTHONPATH="$PWD/src"
python3 -m kofumini.cli run examples/kofumini/hello.kofu
```

期待出力は`42`です。この時点ではmachine codeを実行していません。KIRをPython製reference interpreterで実行しています。

## 1. 言語仕様を小さく固定する

最初のcompilerでclass、GC、module、generic、例外を同時に実装しないことが重要です。KofuMiniは次だけを持ちます。

| 項目 | 仕様 |
|---|---|
| 型 | `Int` = signed 64-bit、`Bool` |
| 宣言 | immutableな`let` |
| 関数 | 型付き引数と戻り値、overloadなし |
| 制御 | 値を返す`if ... else`、短絡`&&`/`||` |
| 演算 | `+ - * / %`、比較、等値、単項`-`/`!` |
| 副作用 | `print(Int)` |
| 安全性 | overflow、0除算、`INT64_MIN / -1`はtrap |

最小文法は次です。`*`は0回以上、`?`は省略可能を表します。

```ebnf
program    = function+ ;
function   = "fn" IDENT "(" params? ")" "->" type "{" statement* "}" ;
params     = IDENT ":" type ("," IDENT ":" type)* ;
type       = "Int" | "Bool" ;
statement  = "let" IDENT ":" type "=" expression ";"
           | "print" "(" expression ")" ";"
           | "return" expression ";" ;
expression = literal | IDENT | call | unary | binary | if_expression
           | "(" expression ")" ;
if_expression = "if" expression "{" expression "}"
                "else" "{" expression "}" ;
```

## 2. Lexer: 文字をtokenへ分ける

入口は`lexer.py`です。lexerは意味を考えず、`fn`、identifier、整数、記号へ分割し、行・列を保存します。

```bash
python3 -m kofumini.cli tokens examples/kofumini/hello.kofu
```

見るポイント:

1. keywordを普通のidentifierより先に確定する。
2. `->`や`==`を`-`、`>`、`=`より先に読む。
3. 最後に`EOF`を置くとparserの停止条件が単純になる。
4. errorには必ずsource位置を含める。

完成実装は`//` commentも処理します。写経するときは、まずcommentなしでtoken testを通し、次のcommitで`//`から行末までを空白と同様に読み飛ばして位置testを追加してください。

## 3. Parser: tokenをASTへ組み立てる

`parser.py`はrecursive descent parserです。statementは先頭keywordで分岐し、二項演算はprecedence climbingで優先順位を扱います。

```bash
python3 -m kofumini.cli ast examples/kofumini/choose.kofu
```

`40 + 2 * 3`は`(40 + (2 * 3))`でなければなりません。`PRECEDENCE`の数字が大きい演算ほど強く結合します。ASTのdata classは`ast_nodes.py`にあり、この段階ではregisterやLLVMを一切考えません。

## 4. Type checker: 間違いを実行前に止める

`typecheck.py`は最初に全関数signatureを集め、その後で各bodyを検査します。これにより後ろで定義した関数も呼べます。

```bash
python3 -m kofumini.cli check examples/kofumini/functions.kofu
python3 -m kofumini.cli check examples/kofumini/type_error.kofu
```

後者は失敗するのが正解です。ここで確定した型は、IR loweringで再推測せず`TypeInfo`から取得します。frontendの型規則とbackendの型表現を混ぜないことが拡張性につながります。

## 5. Typed SSA KIR: 言語とmachineの間を作る

ASTを直接x86へ変換すると、制御フローとCPU制約が絡み合います。そこで`kir.py`の小さな中間表現を挟みます。

```bash
python3 -m kofumini.cli kir examples/kofumini/choose.kofu
```

SSAでは`%v3`のような値を一度だけ定義します。`if`は次の4要素になります。

1. conditionを計算するblock
2. then block
3. else block
4. 合流blockと`phi`

`phi [thenの値, then], [elseの値, else]`は「どのpredecessorから来たかで値を選ぶ」命令です。`lower.py`の`lower_if`を1行ずつ追うと、structured syntaxがCFGへ変わる瞬間を確認できます。

## 6. Verifier: backendの境界で不変条件を守る

`kir.verify`は、block terminator、到達可能性、SSA名の一意性、use-before-def、dominance、operation type、call signature、`phi`のincoming block集合、`return`型を検査します。compilerでは不正なIRを後段へ流さず、生成直後に落とすのが原則です。

次の課題はownership state、memory effect、loop付きCFG、unknown required featureを同じfail-closed境界へ追加することです。

## 7. Reference interpreter: 意味の基準を作る

`interpreter.py`はKIRを直接評価します。これは最適化backendと比較するoracleです。同じ入力について次が一致すべきです。

```text
KIR interpreter result == LLVM/native result == future Kofun backend result
```

compilerがmachine codeを出せても、それだけでは正しさは分かりません。小さく明確なreference semanticsを先に持つと、differential testingが可能になります。

## 8. LLVM emitter: KIRをLLVM IRへ写す

`llvm_emitter.py`は文字列としてLLVM IRを出します。

```bash
python3 -m kofumini.cli llvm examples/kofumini/choose.kofu -o /tmp/choose.ll
```

主な対応は次です。

| KofuMini/KIR | LLVM IR |
|---|---|
| `Int` / `Bool` | `i64` / `i1` |
| checked `+` | `llvm.sadd.with.overflow.i64` + branch to trap |
| comparison | `icmp` |
| `if` | `br` + basic blocks + `phi` |
| function call | `call` |
| return | `ret` |

LLVMの`add`へ安易に`nsw`を付けると、overflow時にtrapではなくpoison semanticsになります。source言語の意味を保つため、この教材ではoverflow intrinsicを明示的に使います。

## 9. Native code: LLVMで最適化・命令選択する

Clangがある環境では次を実行します。

```bash
python3 -m kofumini.cli build \
  examples/kofumini/choose.kofu -O2 -o build/choose
./build/choose
```

Clang driverは`.ll`を受け取り、LLVM optimization、target instruction selection、register allocation、assembly/object生成、system linker呼び出しを行います。段階を観察するには:

```bash
clang -S -O2 /tmp/choose.ll -o /tmp/choose.s
clang -c -O2 /tmp/choose.ll -o /tmp/choose.o
```

## 10. 自分で最初から書く順番

完成codeをコピーせず学ぶ場合、別directoryに次の順で実装します。

1. 整数だけのlexerとtoken test
2. `print(整数);`だけのparserとAST test
3. 定数式interpreter
4. `+ - *`と優先順位
5. 変数とsymbol table
6. `Int`/`Bool`のtype checker
7. functionとcall
8. basic block、branch、SSA、phi
9. KIR verifierとreference interpreter
10. LLVM emitter
11. checked arithmetic
12. differential/random test
13. 独自instruction selectionとregister allocation

各段階で「正常例1つ、境界例1つ、失敗例1つ」をtestにします。次の機能へ進む前に、入力仕様・IR不変条件・期待結果を文章にしてください。

## 11. 何を追加すると本格言語になるか

次はlocal mutable variableとloopです。これによりdominance frontierを使ったphi挿入が必要になります。その後にmemory、array、string、ownership、module、generic、debug informationを順に追加します。GCやasyncはruntime設計まで波及するため、ABI章を理解してから扱います。

## 到達確認

次を説明できれば、最小compilerを一周できています。

- ASTとIRが分かれる理由
- type errorをbackendまで流さない理由
- SSA値が一度だけ定義される利点
- `if`がbranch、block、phiになる過程
- source overflow semanticsとLLVM IR semanticsの違い
- reference interpreterが必要な理由
- object fileとexecutableの違い
