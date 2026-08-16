from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "toy-llvm-language" / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from kofumini.compiler import compile_source  # noqa: E402
from kofumini.interpreter import Interpreter  # noqa: E402


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def summarize(samples: list[float]) -> dict[str, float | int]:
    if not samples:
        raise ValueError("samples must not be empty")
    return {
        "count": len(samples),
        "min_seconds": min(samples),
        "median_seconds": statistics.median(samples),
        "max_seconds": max(samples),
    }


def tool_version(executable: str) -> str:
    completed = subprocess.run(
        [executable, "--version"], text=True, capture_output=True, check=False
    )
    first_line = (completed.stdout or completed.stderr).splitlines()
    return first_line[0] if first_line else "unknown"


def run_program(executable: Path, runs: int) -> dict:
    durations: list[float] = []
    outcomes: list[dict[str, object]] = []
    for _ in range(runs):
        started = time.perf_counter()
        completed = subprocess.run(
            [str(executable)], text=True, capture_output=True, check=False
        )
        durations.append(time.perf_counter() - started)
        outcomes.append(
            {
                "return_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
    stable = all(outcome == outcomes[0] for outcome in outcomes[1:])
    return {"timing": summarize(durations), "outcome": outcomes[0], "stable": stable}


def benchmark_source(
    source_path: Path, clang: str | None, opt_levels: list[str], runs: int
) -> dict:
    source_bytes = source_path.read_bytes()
    source = source_bytes.decode("utf-8")

    frontend_started = time.perf_counter()
    compilation = compile_source(source, source_path.name)
    frontend_seconds = time.perf_counter() - frontend_started
    reference = Interpreter(compilation.kir).run_main()

    result: dict[str, object] = {
        "source": str(source_path),
        "source_sha256": sha256_bytes(source_bytes),
        "frontend_seconds": frontend_seconds,
        "reference": {
            "stdout": reference.stdout,
            "return_code": reference.return_value,
        },
        "native": {},
    }

    native: dict[str, object] = result["native"]  # type: ignore[assignment]
    if clang is None:
        for level in opt_levels:
            native[level] = {"status": "unavailable", "reason": "clang not found"}
        return result

    with tempfile.TemporaryDirectory(prefix="kofumini-bench-") as directory:
        directory_path = Path(directory)
        llvm_path = directory_path / "program.ll"
        llvm_path.write_text(compilation.llvm_ir, encoding="utf-8", newline="\n")
        for level in opt_levels:
            executable = directory_path / f"program-O{level}"
            started = time.perf_counter()
            completed = subprocess.run(
                [clang, str(llvm_path), f"-O{level}", "-o", str(executable)],
                text=True,
                capture_output=True,
                check=False,
            )
            compile_seconds = time.perf_counter() - started
            if completed.returncode != 0:
                native[level] = {
                    "status": "compile_failed",
                    "compile_seconds": compile_seconds,
                    "stderr": completed.stderr,
                }
                continue
            execution = run_program(executable, runs)
            outcome = execution["outcome"]
            correct = bool(
                execution["stable"]
                and outcome["stdout"] == reference.stdout
                and outcome["return_code"] == reference.return_value
            )
            native[level] = {
                "status": "ok" if correct else "mismatch",
                "compile_seconds": compile_seconds,
                "binary_bytes": executable.stat().st_size,
                "execution": execution,
                "correct": correct,
            }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KofuMini LLVM benchmark runner")
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument(
        "--opt-level", action="append", choices=["0", "1", "2", "3", "s"], dest="levels"
    )
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.runs < 1:
        raise SystemExit("--runs must be at least 1")
    levels = list(dict.fromkeys(args.levels or ["0", "2"]))
    clang = shutil.which(args.clang)
    payload = {
        "schema": "compiler-backend-atlas.benchmark/v1",
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "clang_path": clang,
            "clang_version": tool_version(clang) if clang else None,
        },
        "configuration": {"opt_levels": levels, "runs": args.runs},
        "results": [
            benchmark_source(path.resolve(), clang, levels, args.runs)
            for path in args.sources
        ],
    }
    encoded = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(encoded, end="")
    mismatches = [
        entry
        for result in payload["results"]
        for entry in result["native"].values()
        if entry.get("status") == "mismatch"
    ]
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())

