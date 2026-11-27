"""Phase 6 - Code Generation: TAC -> simple assembly-like target code."""
from __future__ import annotations

from .ops import is_const

ARITH = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD", "&&": "AND", "||": "OR"}
COMPARE = {"<": "SETLT", ">": "SETGT", "<=": "SETLE", ">=": "SETGE", "==": "SETEQ", "!=": "SETNE"}


def _opd(x):
    return f"#{x}" if is_const(x) else x


def generate_assembly(code, var_types):
    lines = ["; ---- target: simple 2-register machine (R1, R2) ----", ".data"]
    for name, t in var_types.items():
        lines.append(f"    {name}: {t}")
    lines += ["", ".text"]

    for ins in code:
        op = ins.op
        if op == "label":
            lines.append(f"{ins.res}:")
        elif op == "goto":
            lines.append(f"    JMP   {ins.res}")
        elif op == "iffalse":
            lines.append(f"    CMP   {_opd(ins.a)}, #0")
            lines.append(f"    JE    {ins.res}")
        elif op == "print":
            lines.append(f"    OUT   {_opd(ins.a)}")
        elif op == "=":
            lines.append(f"    LOAD  R1, {_opd(ins.a)}")
            lines.append(f"    STORE {ins.res}, R1")
        elif op == "neg":
            lines += [f"    LOAD  R1, {_opd(ins.a)}", "    NEG   R1", f"    STORE {ins.res}, R1"]
        elif op == "not":
            lines += [f"    LOAD  R1, {_opd(ins.a)}", "    NOT   R1", f"    STORE {ins.res}, R1"]
        elif op in ARITH:
            lines += [f"    LOAD  R1, {_opd(ins.a)}", f"    LOAD  R2, {_opd(ins.b)}",
                      f"    {ARITH[op]:<5} R1, R2", f"    STORE {ins.res}, R1"]
        elif op in COMPARE:
            lines += [f"    LOAD  R1, {_opd(ins.a)}", f"    LOAD  R2, {_opd(ins.b)}",
                      "    CMP   R1, R2", f"    {COMPARE[op]:<5} R1", f"    STORE {ins.res}, R1"]
    lines.append("    HALT")
    return "\n".join(lines)
