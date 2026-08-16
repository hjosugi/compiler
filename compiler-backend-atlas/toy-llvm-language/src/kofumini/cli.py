from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .ast_nodes import to_dict
from .compiler import compile_source
from .errors import CompilerError
from .interpreter import Interpreter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kofuc", description="KofuMini compiler lab")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("tokens", "ast", "check", "kir", "llvm", "run"):
        command = subparsers.add_parser(name)
        command.add_argument("source", type=Path)
        if name == "llvm":
            command.add_argument("-o", "--output", type=Path)

    for name in ("build", "native-run"):
        command = subparsers.add_parser(name)
        command.add_argument("source", type=Path)
        command.add_argument("-O", "--opt-level", choices=["0", "1", "2", "3", "s"], default="2")
        command.add_argument("--clang", default=os.environ.get("CLANG", "clang"))
        if name == "build":
            command.add_argument("-o", "--output", type=Path, required=True)
    return parser


def load(path: Path):
    source = path.read_text(encoding="utf-8")
    return compile_source(source, path.name)


def invoke_clang(llvm_ir: str, output: Path, clang: str, opt_level: str) -> None:
    resolved = shutil.which(clang)
    if resolved is None:
        raise CompilerError(
            f"tool error: {clang!r} was not found; install LLVM/Clang or set CLANG"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kofumini-") as directory:
        llvm_path = Path(directory) / "module.ll"
        llvm_path.write_text(llvm_ir, encoding="utf-8", newline="\n")
        process = subprocess.run(
            [resolved, str(llvm_path), f"-O{opt_level}", "-o", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            raise CompilerError(f"clang failed:\n{process.stderr.rstrip()}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        compilation = load(args.source)
        if args.command == "tokens":
            for token in compilation.tokens:
                print(f"{token.line}:{token.column}\t{token.kind}\t{token.text!r}")
        elif args.command == "ast":
            print(json.dumps(to_dict(compilation.ast), indent=2, ensure_ascii=False))
        elif args.command == "check":
            print("OK")
        elif args.command == "kir":
            print(compilation.kir.render(), end="")
        elif args.command == "llvm":
            if args.output:
                args.output.write_text(compilation.llvm_ir, encoding="utf-8", newline="\n")
            else:
                print(compilation.llvm_ir, end="")
        elif args.command == "run":
            result = Interpreter(compilation.kir).run_main()
            print(result.stdout, end="")
            return result.return_value
        elif args.command == "build":
            invoke_clang(compilation.llvm_ir, args.output, args.clang, args.opt_level)
        elif args.command == "native-run":
            with tempfile.TemporaryDirectory(prefix="kofumini-run-") as directory:
                executable = Path(directory) / "program"
                invoke_clang(compilation.llvm_ir, executable, args.clang, args.opt_level)
                completed = subprocess.run([str(executable)], check=False)
                return completed.returncode
        return 0
    except (CompilerError, OSError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

