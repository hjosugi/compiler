# Compiler pipeline

## 1. Sourceからtyped programまで

Lexerは文字列をtokenへ分けます。Parserはtoken列をASTへします。Name resolutionは同じ文字列がどのdeclarationを参照するかを確定し、type checkerは各expressionの型と許可されたoperationを確定します。

Backendへ渡す前に、最低でも次を確定させます。

- 各symbolの一意なidentity
- 各valueの型
- function signature
- control-flow
- arithmetic semantics: checked、wrap、saturatingのどれか
- memory/ownership/effect semantics
- error時のtrap、exception、resultの扱い

これを曖昧にしたままLLVM IRへ落とすと、LLVMの`poison`やundefined behaviorへ誤って変換しやすくなります。

## 2. High-level IR

High-level IRはsourceより規則的ですが、最適化に必要な言語情報を残します。

Kofunなら次を残す価値があります。

- `read` / `edit` / `take`
- affine resource state
- authority/effect
- concrete enumとexhaustive match
- checked numeric operation
- generic specialization identity
- cleanup obligation

この層でescape analysis、ownership-based alias analysis、specialization、cleanup insertionを行います。

## 3. SSA IR

SSAでは各valueが1度だけ定義されます。

```text
entry:
  %cond = icmp.sgt %left, %right
  branch %cond, then, else
then:
  jump merge
else:
  jump merge
merge:
  %result = phi [%left, then], [%right, else]
  return %result
```

SSAによりdef-use chainが明確になり、constant propagation、dead code elimination、value numberingが行いやすくなります。

## 4. Optimization

代表的なmid-end optimization:

- constant folding / propagation
- sparse conditional constant propagation
- dead code elimination
- common subexpression elimination / GVN
- inlining
- devirtualization
- loop invariant code motion
- induction variable simplification
- loop unroll
- vectorization
- escape analysis / scalar replacement
- tail call transformation

各passには、前提条件、変更するinvariant、無効化するanalysisを明記します。

## 5. Machine lowering

Low IRからmachine codeへは少なくとも次を通ります。

1. operation legalization
2. instruction selection
3. register-bank/class assignment
4. machine-level optimization
5. liveness calculation
6. register allocationとspilling
7. instruction scheduling
8. prologue/epilogue insertion
9. branch relaxationとlayout
10. instruction encoding
11. relocation/object emission

## 6. Linkとruntime

Machine instructionを出しただけでは通常のapplicationになりません。

- symbol resolution
- section layout
- relocation
- static/dynamic library selection
- startup code
- stack unwinding
- exception metadata
- TLS
- sanitizer/runtime helper
- debug information

LLVM ecosystemではMC layer、LLD、compiler-rt、libunwind、libc/libc++などがこの範囲を分担します。

## 7. KofuMiniでの対応

| Pipeline | File |
|---|---|
| Lexer | `kofumini/lexer.py` |
| Parser/AST | `parser.py`, `ast_nodes.py` |
| Type checker | `typecheck.py` |
| typed SSA KIR | `lower.py`, `kir.py` |
| Reference execution | `interpreter.py` |
| LLVM lowering | `llvm_emitter.py` |
| Native driver | `cli.py` |

KofuMiniは小さいため、aliasing、heap、aggregate、exception、debug infoを意図的に含みません。何が省略されているかを明示することも教材の一部です。

