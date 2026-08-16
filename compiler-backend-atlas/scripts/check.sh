#!/bin/sh
set -eu

# Keep the project dependency-free so the complete frontend can be tested with Python alone.
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONPATH="$project_dir/toy-llvm-language/src"
python3 -m unittest discover -s "$project_dir/toy-llvm-language/tests" -v
PYTHONPATH="$project_dir/labs" python3 -m unittest discover \
    -s "$project_dir/labs" -p 'test_*.py' -v
PYTHONPATH="$project_dir/bench" python3 -m unittest discover \
    -s "$project_dir/bench" -p 'test_*.py' -v

# Validate generated LLVM IR when the toolchain is available.
if command -v llvm-as >/dev/null 2>&1; then
    tmp_dir=$(mktemp -d)
    trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM
    python3 -m kofumini.cli llvm \
        "$project_dir/toy-llvm-language/examples/choose.kofu" \
        -o "$tmp_dir/choose.ll"
    llvm-as "$tmp_dir/choose.ll" -o "$tmp_dir/choose.bc"
    if command -v opt >/dev/null 2>&1; then
        opt -passes=verify -disable-output "$tmp_dir/choose.bc"
    fi
else
    echo "SKIP: llvm-as is not installed; Python pipeline tests still passed"
fi
