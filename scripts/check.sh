#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
export PYTHONPATH="$project_dir/src"

python3 -m compileall -q \
    "$project_dir/src" \
    "$project_dir/tutorial" \
    "$project_dir/labs" \
    "$project_dir/benchmarks" \
    "$project_dir/tests"
python3 -m unittest discover -s "$project_dir/tests" -v
python3 "$project_dir/scripts/check_docs.py"

if [ "${SKIP_LLVM:-0}" = "1" ]; then
    echo "SKIP: LLVM checks disabled by SKIP_LLVM=1"
    echo "PASS: Python, tutorial, lab, benchmark-helper, and documentation checks"
    exit 0
fi

missing_tools=""
for tool in llvm-as opt clang; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        missing_tools="$missing_tools $tool"
    fi
done

if [ -n "$missing_tools" ]; then
    if [ "${REQUIRE_LLVM:-0}" = "1" ]; then
        echo "ERROR: required LLVM tools are missing:$missing_tools" >&2
        exit 1
    fi
    echo "SKIP: optional LLVM checks; missing:$missing_tools"
    echo "PASS: Python, tutorial, lab, benchmark-helper, and documentation checks"
    exit 0
fi

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM

for name in hello choose functions short_circuit overflow; do
    python3 -m kofumini.cli llvm \
        "$project_dir/examples/kofumini/$name.kofu" \
        -o "$tmp_dir/$name.ll"
    llvm-as "$tmp_dir/$name.ll" -o "$tmp_dir/$name.bc"
    opt -passes=verify -disable-output "$tmp_dir/$name.bc"
done

python3 -m kofumini.cli build \
    "$project_dir/examples/kofumini/choose.kofu" \
    -O2 -o "$tmp_dir/choose"
"$tmp_dir/choose" > "$tmp_dir/native.stdout"
python3 -m kofumini.cli run \
    "$project_dir/examples/kofumini/choose.kofu" > "$tmp_dir/reference.stdout"
cmp "$tmp_dir/reference.stdout" "$tmp_dir/native.stdout"

echo "PASS: Python and LLVM/native checks"
