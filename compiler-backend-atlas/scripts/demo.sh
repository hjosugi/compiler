#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONPATH="$project_dir/toy-llvm-language/src"
example="$project_dir/toy-llvm-language/examples/choose.kofu"

echo "== Source =="
sed -n '1,200p' "$example"
echo "== Typed KIR =="
python3 -m kofumini.cli kir "$example"
echo "== LLVM IR (first 100 lines) =="
python3 -m kofumini.cli llvm "$example" | sed -n '1,100p'
echo "== Reference interpreter =="
python3 -m kofumini.cli run "$example"

if command -v clang >/dev/null 2>&1; then
    echo "== Native executable through LLVM/Clang =="
    python3 -m kofumini.cli native-run "$example" -O2
else
    echo "SKIP: clang is not installed"
fi

