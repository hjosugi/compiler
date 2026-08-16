#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
    echo "usage: scripts/package.sh vMAJOR.MINOR.PATCH" >&2
    exit 2
fi

version=$1
case "$version" in
    v[0-9]*.[0-9]*.[0-9]*) ;;
    *)
        echo "ERROR: version must look like v1.0.0" >&2
        exit 2
        ;;
esac

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "ERROR: package only from a clean tracked worktree" >&2
    exit 1
fi

name="compiler-atlas-${version#v}"
mkdir -p dist
git archive --format=zip --prefix="$name/" HEAD -o "dist/$name.zip"
(
    cd dist
    sha256sum "$name.zip" > "$name.zip.sha256"
)
unzip -t "dist/$name.zip" >/dev/null

printf '%s\n' "dist/$name.zip"
cat "dist/$name.zip.sha256"
