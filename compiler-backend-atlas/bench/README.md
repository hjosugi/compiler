# Benchmark runner

KofuMiniのreference interpreterと、Clang/LLVM native pathを同じsourceで比較します。これはLLVMより速いという主張を作るtoolではなく、correctnessを満たしたcaseについてcompile latency、binary size、runtimeを保存する最小基盤です。

```bash
export PYTHONPATH="$PWD/toy-llvm-language/src"
python3 bench/runner.py \
  toy-llvm-language/examples/hello.kofu \
  toy-llvm-language/examples/choose.kofu \
  --opt-level 0 --opt-level 2 --runs 7 \
  --output build/bench.json
```

Clangがなければreference結果だけを記録し、native結果は`unavailable`になります。JSONにはplatform、Python、compiler path/version、source SHA-256、各run、median、stdout/exit一致を保存します。

比較時はhardware/OSを固定し、CPU governor、thermal、cold/warm cacheを別途manifestに記録してください。異なるmachineの小さい時間差を直接比較しません。

