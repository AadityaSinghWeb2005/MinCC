"""Shared operator semantics (used by the optimizer AND the virtual machine)."""
from __future__ import annotations

import math
import re

NUM_RE = re.compile(r"-?\d+(\.\d+)?([eE][-+]?\d+)?$")
INT_RE = re.compile(r"-?\d+$")

ARITH_OPS = {"+", "-", "*", "/", "%"}
REL_OPS = {"<", ">", "<=", ">=", "==", "!="}
LOGIC_OPS = {"&&", "||"}
BINARY_OPS = ARITH_OPS | REL_OPS | LOGIC_OPS
UNARY_OPS = {"neg", "not"}


def is_const(x):
    return isinstance(x, str) and NUM_RE.match(x) is not None


def is_int_lit(x, value):
    return isinstance(x, str) and INT_RE.match(x) is not None and int(x) == value


def parse_const(x):
    return int(x) if INT_RE.match(x) else float(x)


def fmt_const(v):
    return repr(v)


def fmt_value(v):
    if isinstance(v, float):
        return str(round(v, 6))
    return str(v)


def eval_binop(op, a, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            raise ZeroDivisionError("division by zero")
        if isinstance(a, int) and isinstance(b, int):      # C-style truncation
            q = abs(a) // abs(b)
            return q if (a < 0) == (b < 0) else -q
        return a / b
    if op == "%":
        if b == 0:
            raise ZeroDivisionError("modulo by zero")
        if isinstance(a, int) and isinstance(b, int):
            r = abs(a) % abs(b)
            return -r if a < 0 else r
        return math.fmod(a, b)
    if op == "<":
        return int(a < b)
    if op == ">":
        return int(a > b)
    if op == "<=":
        return int(a <= b)
    if op == ">=":
        return int(a >= b)
    if op == "==":
        return int(a == b)
    if op == "!=":
        return int(a != b)
    if op == "&&":
        return int(bool(a) and bool(b))
    if op == "||":
        return int(bool(a) or bool(b))
    raise ValueError(f"Unknown operator {op}")


def eval_unop(op, a):
    if op == "neg":
        return -a
    if op == "not":
        return int(not a)
    raise ValueError(f"Unknown unary operator {op}")
