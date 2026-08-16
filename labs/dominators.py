from __future__ import annotations

from collections import defaultdict


def compute_dominators(entry: str, successors: dict[str, tuple[str, ...]]) -> dict[str, set[str]]:
    """Compute dominator sets with the classic iterative data-flow algorithm."""
    nodes = set(successors)
    for targets in successors.values():
        nodes.update(targets)
    predecessors: dict[str, set[str]] = defaultdict(set)
    for source, targets in successors.items():
        for target in targets:
            predecessors[target].add(source)

    dominators = {node: ({node} if node == entry else set(nodes)) for node in nodes}
    changed = True
    while changed:
        changed = False
        for node in sorted(nodes - {entry}):
            preds = predecessors[node]
            shared = set.intersection(*(dominators[pred] for pred in preds)) if preds else set()
            updated = {node} | shared
            if updated != dominators[node]:
                dominators[node] = updated
                changed = True
    return dominators


def main() -> None:
    cfg = {
        "entry": ("then", "else"),
        "then": ("merge",),
        "else": ("merge",),
        "merge": ("exit",),
        "exit": (),
    }
    for block, doms in sorted(compute_dominators("entry", cfg).items()):
        print(f"{block}: {', '.join(sorted(doms))}")


if __name__ == "__main__":
    main()
