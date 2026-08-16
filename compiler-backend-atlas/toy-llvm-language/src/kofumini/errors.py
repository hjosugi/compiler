from __future__ import annotations


class CompilerError(Exception):
    """Base class for deterministic user-facing compiler errors."""


class LexError(CompilerError):
    pass


class ParseError(CompilerError):
    pass


class TypeCheckError(CompilerError):
    pass


class VerificationError(CompilerError):
    pass


class RuntimeTrap(CompilerError):
    pass

