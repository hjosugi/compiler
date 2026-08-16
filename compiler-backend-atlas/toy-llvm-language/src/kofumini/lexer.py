from __future__ import annotations

from .errors import LexError
from .tokens import KEYWORDS, Token


TWO_CHAR_TOKENS = {
    "->": "ARROW",
    "==": "EQEQ",
    "!=": "NE",
    "<=": "LE",
    ">=": "GE",
    "&&": "ANDAND",
    "||": "OROR",
}

ONE_CHAR_TOKENS = {
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    ",": "COMMA",
    ":": "COLON",
    ";": "SEMI",
    "=": "EQ",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "<": "LT",
    ">": "GT",
    "!": "BANG",
}


def lex(source: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    line = 1
    column = 1

    while i < len(source):
        ch = source[i]

        if ch in " \t\r":
            i += 1
            column += 1
            continue
        if ch == "\n":
            i += 1
            line += 1
            column = 1
            continue
        if source.startswith("//", i):
            while i < len(source) and source[i] != "\n":
                i += 1
                column += 1
            continue

        start_line = line
        start_column = column
        pair = source[i : i + 2]
        if pair in TWO_CHAR_TOKENS:
            tokens.append(Token(TWO_CHAR_TOKENS[pair], pair, line, column))
            i += 2
            column += 2
            continue

        if ch.isdigit():
            start = i
            while i < len(source) and source[i].isdigit():
                i += 1
                column += 1
            tokens.append(Token("INT", source[start:i], start_line, start_column))
            continue

        if ch.isalpha() or ch == "_":
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                i += 1
                column += 1
            text = source[start:i]
            tokens.append(Token(KEYWORDS.get(text, "IDENT"), text, start_line, start_column))
            continue

        if ch in ONE_CHAR_TOKENS:
            tokens.append(Token(ONE_CHAR_TOKENS[ch], ch, line, column))
            i += 1
            column += 1
            continue

        raise LexError(f"lex error at {line}:{column}: unexpected character {ch!r}")

    tokens.append(Token("EOF", "", line, column))
    return tokens

