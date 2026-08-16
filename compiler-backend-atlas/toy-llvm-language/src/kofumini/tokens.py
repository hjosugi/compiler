from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    text: str
    line: int
    column: int

    def location(self) -> str:
        return f"{self.line}:{self.column}"


KEYWORDS = {
    "fn": "FN",
    "let": "LET",
    "return": "RETURN",
    "print": "PRINT",
    "if": "IF",
    "else": "ELSE",
    "true": "TRUE",
    "false": "FALSE",
    "Int": "INT_TYPE",
    "Bool": "BOOL_TYPE",
}

