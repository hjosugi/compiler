# 段階演習と完成条件

完成codeを読むだけで終わらないための実装課題です。各演習は前段だけに依存し、正常・境界・error testを追加してから次へ進みます。

## Level 1: Frontend

### 1. Tokenを1つ追加

既存の`// comment`の次に`/* ... */` commentを実装します。KofuMini v1のidentifierはASCII限定なので、その境界を維持するか、Unicode normalizationとconfusable対策を含む新仕様を作ります。

完成条件:

- line/columnがcomment後も正しい。
- 閉じていないblock commentが位置付きerrorになる。
- ASCII/Unicodeの境界例が仕様どおりtokenizeまたはrejectされる。

### 2. Unary operator

`~Int -> Int`を追加します。lexer token、AST表現、parser precedence、type rule、KIR op、interpreter、LLVM `xor i64 value, -1`まで通します。

完成条件: `~0`、二重適用、Boolへの誤適用をtest。

### 3. `else if` sugar

syntaxだけを追加し、既存のnested `IfExpr`へdesugarします。新しいbackend operationは増やしません。

完成条件: AST dumpでnested ifとなり、KIR/LLVM変更を最小化。

## Level 2: IR

### 4. KIR use-def verifier

各operandがparameter、literal、またはSSA definitionであり、そのdefinitionがuseをdominateすることを検査します。

完成条件: same blockのuse-before-def、別branchだけのdefinition、unknown valueを拒否。

### 5. Constant folding

pureなconstant operationをfoldします。checked overflow/div-by-zeroはconstantにせずcompile-time diagnosticまたはexplicit trapにします。どちらかをspecへ固定します。

完成条件: pass前後をinterpreterで比較し、KIR verifierを両方通す。

### 6. Dead code elimination

結果が未使用のpure instructionだけ削除します。`print`、call、trapし得るchecked opを削除しません。

完成条件: effect分類をhard-codeの散在ではなくoperation propertyとして定義。

## Level 3: Controlとmutable state

### 7. `while`

ASTへloopを追加し、header/body/exit blockへlowerします。最初はlocal mutationなしで、関数callをconditionに使います。

完成条件: zero iteration、複数iteration、short circuit、returnとの関係を定義。

### 8. Mutable localとmem2reg

最初は`alloca/load/store`相当のKIRへlowerし、後からdominance frontierでphiを挿入してSSAへ変換します。

完成条件: diamond、loop-carried value、nested loopでinterpreter結果一致。

## Level 4: Backend

### 9. Stack-machine backend

KIRから小さな独自bytecodeを生成し、VMで実行します。instructionはconstant、local、arithmetic、branch、call、return、printから開始します。

完成条件: KIR interpreter、bytecode VM、LLVM nativeの三者一致。

### 10. x86-64 assembly backend

integer subsetをSystem V assembly textへ出します。最初は全valueをstackへ置き、次にlinear scanを接続します。

完成条件: assembly/objectのdisassembly golden、ABI call test、spill test。

### 11. ELF relocatable writer

`.text`、symbol table、string table、relocationを持つ最小ELF64 objectを生成します。

完成条件: `readelf`がerrorなし、LLD/system linkerでlink、same result。

## Level 5: LLVMを超える実験

### 12. Baseline latency

`benchmarks/runner.py`へdirect backendを追加し、LLVM O0と同一process/cold processを分けて測ります。

完成条件:

- correctness不一致caseをperformance集計から隠さない。
- toolchain commit、flags、hardware、raw runsをJSONに保存。
- medianだけでなくdistributionとbinary sizeを報告。

### 13. Ownership optimization

unique arena objectをKIRで表現し、escapeしないobjectをstack/scalarへ昇格します。

完成条件: alias preconditionをverifier/validatorで確認し、escaping/aliasing negative testを持つ。

### 14. Local superoptimizer

pure integer basic blockだけを対象に、equivalent instruction sequenceを探索します。timeout/node budgetとtranslation validatorを必須にします。

完成条件: 見つけたrewrite、証明condition、cost modelをartifactとして保存。

## Review template

各課題のPR/commitに次を書きます。

```text
Semantic change:
Grammar/type rule:
IR before/after:
New invariant:
Normal/boundary/error tests:
Reference/direct/LLVM comparison:
Compile-time/runtime/size impact:
Known unsupported cases:
```

答えをcode量で評価しません。semanticが文章化され、errorを早い層で検出し、独立oracleで結果を比較できることが完成条件です。
