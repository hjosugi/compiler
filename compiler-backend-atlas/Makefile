.PHONY: check demo tokens ast kir llvm run native clean

PYTHONPATH := toy-llvm-language/src
EXAMPLE := toy-llvm-language/examples/choose.kofu

check:
	PYTHONPATH=$(PYTHONPATH) sh scripts/check.sh

demo:
	PYTHONPATH=$(PYTHONPATH) sh scripts/demo.sh

tokens:
	PYTHONPATH=$(PYTHONPATH) python3 -m kofumini.cli tokens $(EXAMPLE)

ast:
	PYTHONPATH=$(PYTHONPATH) python3 -m kofumini.cli ast $(EXAMPLE)

kir:
	PYTHONPATH=$(PYTHONPATH) python3 -m kofumini.cli kir $(EXAMPLE)

llvm:
	PYTHONPATH=$(PYTHONPATH) python3 -m kofumini.cli llvm $(EXAMPLE)

run:
	PYTHONPATH=$(PYTHONPATH) python3 -m kofumini.cli run $(EXAMPLE)

native:
	mkdir -p build
	PYTHONPATH=$(PYTHONPATH) python3 -m kofumini.cli build $(EXAMPLE) -O2 -o build/choose
	./build/choose

clean:
	rm -rf build

