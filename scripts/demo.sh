#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONPATH="$project_dir/src"
example="$project_dir/examples/kofumini/choose.kofu"

printf '%s\n' "== Tutorial calculator =="
python3 "$project_dir/tutorial/stage1_calc.py" "1 + 2 * (3 - 1)"
printf '%s\n' "== KofuMini source =="
sed -n '1,200p' "$example"
printf '%s\n' "== Typed KIR =="
python3 -m kofumini.cli kir "$example"
printf '%s\n' "== LLVM IR (first 100 lines) =="
python3 -m kofumini.cli llvm "$example" | sed -n '1,100p'
printf '%s\n' "== KIR reference interpreter =="
python3 -m kofumini.cli run "$example"

if command -v clang >/dev/null 2>&1; then
    printf '%s\n' "== Native executable through LLVM/Clang =="
    python3 -m kofumini.cli native-run "$example" -O2
else
    printf '%s\n' "SKIP: clang is not installed"
fi
