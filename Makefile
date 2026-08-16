.PHONY: check check-python check-llvm lint demo tutorial tokens ast kir llvm run native benchmark-smoke package clean

PYTHON ?= python3
VERSION ?= v1.1.0
PYTHONPATH := src
EXAMPLE := examples/kofumini/choose.kofu
export PYTHONPATH

check:
	sh scripts/check.sh

check-python:
	SKIP_LLVM=1 sh scripts/check.sh

check-llvm:
	REQUIRE_LLVM=1 sh scripts/check.sh

lint:
	$(PYTHON) -m ruff check src tests benchmarks labs scripts
	$(PYTHON) -m ruff format --check src tests benchmarks labs scripts
	$(PYTHON) -m mypy src/kofumini

demo:
	sh scripts/demo.sh

tutorial:
	$(PYTHON) tutorial/stage1_calc.py "1 + 2 * (3 - 1)"
	$(PYTHON) tutorial/stage2_interp.py tutorial/examples/countdown.mini
	$(PYTHON) tutorial/stage3_functions.py tutorial/examples/fib.mini
	$(PYTHON) tutorial/stage4_typecheck.py tutorial/examples/fib.mini
	$(PYTHON) tutorial/stage5_bytecode.py tutorial/examples/fib.mini

tokens:
	$(PYTHON) -m kofumini.cli tokens $(EXAMPLE)

ast:
	$(PYTHON) -m kofumini.cli ast $(EXAMPLE)

kir:
	$(PYTHON) -m kofumini.cli kir $(EXAMPLE)

llvm:
	$(PYTHON) -m kofumini.cli llvm $(EXAMPLE)

run:
	$(PYTHON) -m kofumini.cli run $(EXAMPLE)

native:
	mkdir -p build
	$(PYTHON) -m kofumini.cli build $(EXAMPLE) -O2 -o build/choose
	./build/choose

benchmark-smoke:
	@$(PYTHON) benchmarks/runner.py --runs 1 --opt-level 0 --opt-level 2 $(EXAMPLE)

package:
	sh scripts/package.sh $(VERSION)

clean:
	rm -rf build dist src/kofumini/__pycache__ tests/__pycache__ tutorial/__pycache__ labs/__pycache__ benchmarks/__pycache__
