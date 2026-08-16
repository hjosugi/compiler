from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .ast_nodes import to_dict
from .compiler import check_source, compile_source, lower_source, parse_source, tokenize_source
from .errors import CompilerError
from .interpreter import Interpreter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kofuc", description="KofuMini compiler lab")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in (
        "tokens",
        "ast",
        "check",
        "kir",
        "kir-json",
        "kir-hash",
        "llvm",
        "run",
    ):
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def invoke_clang(llvm_ir: str, output: Path, clang: str, opt_level: str) -> None:
    resolved = shutil.which(clang)
    if resolved is None:
        raise CompilerError(f"tool error: {clang!r} was not found; install LLVM/Clang or set CLANG")
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
        source = args.source.read_text(encoding="utf-8")
        if args.command == "tokens":
            for token in tokenize_source(source):
                print(f"{token.line}:{token.column}\t{token.kind}\t{token.text!r}")
        elif args.command == "ast":
            parsed = parse_source(source)
            print(json.dumps(to_dict(parsed.ast), indent=2, ensure_ascii=False))
        elif args.command == "check":
            check_source(source)
            print("OK")
        elif args.command in {"kir", "kir-json", "kir-hash", "run"}:
            lowered = lower_source(source)
            if args.command == "kir":
                print(lowered.kir.render(), end="")
            elif args.command == "kir-json":
                print(lowered.kir.canonical_json())
            elif args.command == "kir-hash":
                print(f"module {lowered.kir.content_hash()}")
                for name, digest in lowered.kir.function_hashes().items():
                    print(f"function {name} {digest}")
            else:
                result = Interpreter(lowered.kir).run_main()
                print(result.stdout, end="")
                return result.return_value
        elif args.command in {"llvm", "build", "native-run"}:
            compilation = compile_source(source, args.source.name)
            if args.command == "llvm":
                if args.output:
                    write_text(args.output, compilation.llvm_ir)
                else:
                    print(compilation.llvm_ir, end="")
            elif args.command == "build":
                invoke_clang(compilation.llvm_ir, args.output, args.clang, args.opt_level)
            else:
                with tempfile.TemporaryDirectory(prefix="kofumini-run-") as directory:
                    executable = Path(directory) / "program"
                    invoke_clang(compilation.llvm_ir, executable, args.clang, args.opt_level)
                    completed = subprocess.run([str(executable)], check=False)
                    return completed.returncode
        else:
            raise AssertionError(args.command)
        return 0
    except (CompilerError, OSError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
