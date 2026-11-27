"""Phase 1 - Lexical Analysis (Scanner).

Converts the raw source text into a stream of tokens using regular expressions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

KEYWORDS = {"int", "float", "if", "else", "while", "print"}

# Order matters: longer / more specific patterns first.
TOKEN_SPEC = [
    ("COMMENT", r"//[^\n]*"),
    ("FLOAT", r"\d+\.\d+"),
    ("INT", r"\d+"),
    ("ID", r"[A-Za-z_][A-Za-z_0-9]*"),
    ("OP2", r"==|!=|<=|>=|&&|\|\|"),
    ("OP", r"[+\-*/%<>=!]"),
    ("PUNCT", r"[(){};]"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t\r]+"),
    ("MISMATCH", r"."),
]
TOKEN_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int


@dataclass
class LexError:
    message: str
    line: int
    col: int


def tokenize(source: str):
    """Return (tokens, errors)."""
    tokens, errors = [], []
    line, line_start = 1, 0

    for m in TOKEN_REGEX.finditer(source):
        kind, text = m.lastgroup, m.group()
        col = m.start() - line_start + 1

        if kind == "NEWLINE":
            line += 1
            line_start = m.end()
            continue
        if kind in ("SKIP", "COMMENT"):
            continue
        if kind == "MISMATCH":
            errors.append(LexError(f"Invalid character '{text}'", line, col))
            continue

        if kind == "ID":
            ttype = "KEYWORD" if text in KEYWORDS else "IDENTIFIER"
        elif kind == "INT":
            ttype = "INTEGER"
        elif kind == "FLOAT":
            ttype = "FLOAT"
        elif kind in ("OP", "OP2"):
            ttype = "OPERATOR"
        else:
            ttype = "SEPARATOR"
        tokens.append(Token(ttype, text, line, col))

    tokens.append(Token("EOF", "", line, len(source) - line_start + 1))
    return tokens, errors
