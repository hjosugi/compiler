# GUIDE — 言語処理系をゼロから作る 5 段階

各 stage は単体で動く完全な処理系。前の stage との diff がそのまま「その回で学ぶこと」になる。

```
Stage1  文字列 → トークン → AST → 評価           (電卓)
Stage2  + 文・変数・制御フロー・スコープ          (インタプリタ)
Stage3  + 関数・再帰・コールスタック              (Mini 言語完成)
Stage4  + 静的検査 (実行せずにエラーを見つける)
Stage5  AST → バイトコード → VM                   (ここから「コンパイラ」)
Stage6  → compiler-backend-compendium へ接続      (LLVM IR / ネイティブ)
```

読み方: 各 stage のソースを上から読む → 動かす → diff を取る → 演習を 1 つやる。

```sh
python3 stage1_calc.py "1 + 2 * (3 - 1)"
python3 stage2_interp.py examples/countdown.mini
python3 stage3_functions.py examples/fib.mini
python3 stage4_typecheck.py examples/bad_int_condition.mini   # 弾かれる
python3 stage5_bytecode.py --dis examples/fib.mini            # バイトコードを見る
diff stage2_interp.py stage3_functions.py                     # 「関数」の差分だけが見える
```

---

## Stage 1 — 電卓: 処理系の骨格

言語処理系は必ずこの 3 段から始まる。

```
"1 + 2 * 3"
   │ 字句解析 (lexer): 文字のかたまりに名前を付ける
   ▼
[num 1] [+] [num 2] [*] [num 3]
   │ 構文解析 (parser): 木にする
   ▼
        (+)
       /   \
   (num 1)  (*)
           /   \
      (num 2) (num 3)
   │ 評価 (evaluator)
   ▼
    7
```

### 文法と BNF
文法は BNF (バッカス記法) で書く。`:=` の右に「この形が許される」を列挙する。

```
expr    := term  (('+' | '-') term)*
term    := unary (('*' | '/' | '%') unary)*
unary   := '-' unary | primary
primary := NUMBER | '(' expr ')'
```

### 再帰下降 = 文法をそのまま関数にする
BNF の 1 規則 = 1 つの parse_ 関数。これが再帰下降 (recursive descent)。
手書きパーサの事実上の標準で、clang も Go も V8 も再帰下降。

### 優先順位はどこにも「数値」として書かれていない
parse_expr が operand を parse_term に頼む、という**呼び出しの階層そのもの**が
優先順位になる。`1 + 2 * 3` では、`+` が左右を手に入れる前に
parse_term の中で `2 * 3` が先に木になっている。

```
parse_expr        ← 弱い演算子 (+ -) を束ねる
  └ parse_term    ← 強い演算子 (* / %) を先に束ねる
      └ parse_unary
          └ parse_primary   ← 最強 (リテラル・括弧)
```

### 左結合は while で作る
`node = (op, node, 右)` を while で繰り返すと `1-2-3` は `((1-2)-3)` になる。
再帰で書くと右結合になってしまう (演習: 右結合の `^` べき乗を足して確認)。

**演習**: (a) `**` (右結合) を追加 (b) 小数対応 (c) エラー位置 (何文字目か) を出す

---

## Stage 2 — 文・変数・制御フロー

### 文と式
式 (expression) は値に**なる**。文 (statement) は何かを**する**。
`1 + 2` は式、`print(x);` は文。この区別が曖昧な言語 (すべてが式の Lisp や
Kofun の方針) もあり、それは言語設計の選択。

### 環境 (environment) = 変数の住所録
「変数名 → 値」の辞書。ブロック `{}` に入るたびに子環境を作って親へ
チェーンする。名前解決は内側から外側へ辿る。

```
グローバル環境          { n: 5 }
    ▲ parent
while 本体の環境        { msg: 50 }     ← let msg はここに定義される
```

`}` を抜けたら子環境ごと捨てる — これがブロックスコープの実装のすべて。
なお前回 zip の minic.py は関数フラットスコープ (子環境なし)。
diff すると「スコープは意味論であり、実装は 1 クラス」だと分かる。

### 制御フローは今はホスト言語からの借り物
Mini の while は Python の while で回している。Stage 5 でこの借りを返す
(ジャンプ命令で自作する)。「インタプリタは制御フローを借金する」と覚える。

**演習**: (a) `for` を while への脱糖 (desugar) で実装 (b) `&&` `||` を短絡評価で
(c) 未定義変数エラーに行番号を出す (AST に行番号を持たせる改造)

---

## Stage 3 — 関数: フレームとコールスタック

### 呼び出し = 新しい環境を作ること
`fib(9)` の実行とは「params → args を束縛した新しい環境 (= スタックフレーム) を
作って本体を実行する」こと。再帰は特別扱い不要 — フレームが呼び出しごとに
別物だから、勝手に正しく動く。

```
call fib(3)
  frame{n:3} → call fib(2)
                 frame{n:2} → call fib(1)
                                frame{n:1} → return 1
```

いまコールスタックは Python の再帰そのもの (借り物その 2)。
Stage 5 の演習で明示的なフレーム配列にする — それが末尾呼出最適化 (TCO) の入口。

### return はなぜ例外で実装するのか
return は「どれだけ深くネストした文の中からでも、関数の呼び出し元まで一気に
脱出する」。この動的な脱出範囲は、ホスト言語の例外の性質と完全に一致する。
だからツリーウォーク型インタプリタは例外で return を実装する (Crafting
Interpreters も同じ)。break/continue も同じ手で作れる (演習)。

**演習**: (a) break/continue (b) 関数を値にする (変数に入れて呼ぶ) →
そのとき「定義時の環境」を関数に持たせると**クロージャ**になる

---

## Stage 4 — 静的検査: 実行せずに間違いを見つける

### static の意味
Stage 3 までは、未定義変数も型違いも「実行がそこに到達したら」しか分からない。
検査パスを parse と実行の間に挟むと、**プログラム全体を実行前に**却下できる。
これが静的 (static)。テストが通らない経路のバグまで捕まえられるのが価値。

### 型付け規則の読み方
型システムの論文に出る `Γ ⊢ e : τ` は「環境 Γ のもとで式 e は型 τ を持つ」。
Stage 4 の check_expr はこの規則をそのまま Python にしたもの。

```
Γ ⊢ e1 : int    Γ ⊢ e2 : int          ← 前提 (上段)
─────────────────────────────
Γ ⊢ e1 + e2 : int                      ← 結論 (下段)
```

### bool を分けた理由
Mini 本来の意味論は C 風「0 が偽」。Stage 4 はあえて int と bool を分離し、
`if (1)` を却下する。型を分けるほど**間違いのクラスを 1 つ実行前に消せる**
— これが型システムを濃くする動機で、Kofun の read/edit/take も
「エイリアスの間違いを型で実行前に消す」という同じ思想の延長にある。

### エラーメッセージは仕様の一部
「何が・どこで・どうすべきか」を言えるかは checker の設計で決まる。
行番号を AST に持たせる改造 (Stage 2 演習 c) をここでやると効果が出る。

**演習**: (a) bool 変数同士の `==` を許可 (b) 関数の戻り値型宣言 `fn f(x) -> bool`
(c) 「宣言して未使用」警告 (d) 型推論: `let` の型を右辺から決めているのは
実はもう推論 — これを関数境界まで広げると Hindley-Milner の入口

---

## Stage 5 — バイトコード: ここからコンパイラ

### 木を歩くのをやめ、命令列に翻訳する
Stage 3 までは実行のたびに AST を歩き直していた。Stage 5 は**一度だけ**
AST を平坦な命令列に翻訳し、以後は命令列だけを実行する。
「翻訳を実行から分離した」瞬間、それはコンパイラと呼ばれる。
CPython・JVM・Lua はまさにこのモデル。

### 式の平坦化 = 後順走査
```
      (*)                CONST 1
     /   \               CONST 2
   (+)   (x)      →      BINOP +      ← 子を先に、自分を最後に
   /  \                  LOAD x
 (1)  (2)                BINOP *
```
スタックマシンでは「オペランドを先に積み、演算子が最後」— これだけ。

### 制御フローの借金を返す: ジャンプと backpatch
```
if (c) { A } else { B }        while (c) { A }

    <c>                        top: <c>
    JMPF else ──┐                   JMPF end ──┐
    <A>         │                   <A>        │
    JMP  end ──┐│                   JMP top    │
else: <B>    ◄─┼┘              end:          ◄─┘
end:         ◄─┘
```
前方ジャンプは飛び先がまだ分からないので、穴 (None) を掘っておいて
飛び先が確定した瞬間に埋める — **backpatching**。実機コード生成でも
リンカの再配置でも、この「あとで埋める」は同じ形で現れる。

### VM = 手作りの CPU
pc (program counter)・オペランドスタック・変数表。while ループで命令を
1 つずつ読む — CPU のフェッチ・実行サイクルの縮小模型。
`--dis` で fib のバイトコードを眺めると、LLVM IR (`minilang/run.sh -ir`) と
構造が同型だと分かるはず。

**演習**: (a) CALL の再帰を明示的フレームスタックに変える →
末尾位置の CALL でフレームを積まない = **TCO の実装** (Kofun の意味論要件の縮小版)
(b) 変数名を番号スロットに変える (LOAD "n" → LOAD 0) = レジスタ割付の前身
(c) 定数畳み込み: CONST a; CONST b; BINOP + を CONST (a+b) に潰すピープホール最適化

---

## Stage 6 — ここから先: compendium への接続

この教材の言語 Mini は compiler-backend-compendium の minilang と同一。
つまり同じ AST から 4 本の「後ろ半分」が生えている:

| 後ろ半分 | 場所 | 実行形態 |
|---|---|---|
| ツリーウォーク | stage3_functions.py | その場で木を歩く |
| バイトコード VM | stage5_bytecode.py | 命令列 + 仮想機械 |
| LLVM IR 経由ネイティブ | compendium/minilang/minic.py | 最適化と codegen を LLVM に委譲 |
| 直接ネイティブ | compendium/hands-on/direct-backend/ | 全部自分で払う |

Kofun との対応: lexer/parser (済) = Stage1-3、型・所有権検査 = Stage4 の本格版、
KIR = Stage5 のバイトコードの本格版 (typed・SSA・直列化可能)、
C11 / native / wasm32 / llvm-hosted backend = Stage6 の 4 分岐そのもの。
この階段を登り切った時点で、KIR 計画の全部品に「触ったことがある」状態になる。

## 次に読むもの (この順で)
1. Crafting Interpreters (Nystrom, 無料公開) — Stage1-5 の完全版
2. Ghuloum, "An Incremental Approach to Compiler Construction" (2006) —
   本教材と同じ「毎段動く」思想でネイティブまで
3. chibicc (Rui Ueyama) — コミット単位で成長する C コンパイラ。diff 読みの最高峰
4. compendium/docs/ 01 → 05 → 02 の順

## 言語設計ミニノート
- 文法は再帰下降で素直に書ける形 (先読み 1 トークンで分岐が決まる ≒ LL(1)) に
  保つと、実装もエラーメッセージも楽になる。Kofun の「ひねらない構文」方針は
  実装コスト面でも正しい
- 意味論は先に散文で書く。「0 は偽か」「除算は切り捨て方向どちらか」を
  コードで決めると、後から仕様が実装の人質になる
- 機能は「消せるか」で審査する。脱糖 (for → while) で作れるものはコアに入れない
  — コアが小さいほど検査器もバックエンドも小さい
