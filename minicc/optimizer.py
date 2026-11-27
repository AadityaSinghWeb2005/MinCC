"""Phase 5 - Code Optimization on Three Address Code.

Techniques implemented:
  * Constant propagation
  * Constant folding
  * Algebraic simplification (x+0, x*1, x-0, x/1)
  * Constant-condition branch elimination
  * Copy/temporary elimination
  * Dead (unused) temporary elimination
  * Unused label removal, unreachable code removal, jump-to-next removal
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import replace

from .ops import (BINARY_OPS, UNARY_OPS, eval_binop, eval_unop, fmt_const,
                  is_const, is_int_lit, parse_const)
from .tac import TAC

TEMP_RE = re.compile(r"\$t\d+$")
DEFINING = BINARY_OPS | UNARY_OPS | {"="}


def is_temp(name):
    return isinstance(name, str) and TEMP_RE.match(name) is not None


def _note(log, technique, change):
    log.append({"Technique": technique, "Change": change})


def _safe_binary(op, a, b):
    try:
        v = eval_binop(op, parse_const(a), parse_const(b))
    except (ZeroDivisionError, ValueError, OverflowError):
        return None
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _safe_unary(op, a):
    try:
        v = eval_unop(op, parse_const(a))
    except (ValueError, OverflowError):
        return None
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _simplify(ins):
    op, a, b = ins.op, ins.a, ins.b
    if op not in BINARY_OPS:
        return None
    if op == "+" and is_int_lit(b, 0):
        return a
    if op == "+" and is_int_lit(a, 0):
        return b
    if op == "-" and is_int_lit(b, 0):
        return a
    if op == "*" and is_int_lit(b, 1):
        return a
    if op == "*" and is_int_lit(a, 1):
        return b
    if op == "/" and is_int_lit(b, 1):
        return a
    return None


def _fold_and_propagate(code, var_types, log):
    out, consts = [], {}
    for original in code:
        ins = replace(original)
        if ins.op == "label":
            consts.clear()          # a label starts a new basic block
            out.append(ins)
            continue

        before = str(ins)

        # 1) constant propagation
        for attr in ("a", "b"):
            v = getattr(ins, attr)
            if v is not None and v in consts:
                setattr(ins, attr, consts[v])
        if str(ins) != before:
            _note(log, "Constant propagation", f"{before}   →   {ins}")

        # 2) constant folding / algebraic simplification
        folded = None
        if ins.op in BINARY_OPS and is_const(ins.a) and is_const(ins.b):
            folded = _safe_binary(ins.op, ins.a, ins.b)
        elif ins.op in UNARY_OPS and is_const(ins.a):
            folded = _safe_unary(ins.op, ins.a)

        if folded is not None:
            new = TAC("=", fmt_const(folded), None, ins.res)
            _note(log, "Constant folding", f"{ins}   →   {new}")
            ins = new
        else:
            simp = _simplify(ins)
            if simp is not None:
                new = TAC("=", simp, None, ins.res)
                _note(log, "Algebraic simplification", f"{ins}   →   {new}")
                ins = new

        # 3) branches with constant conditions
        if ins.op == "iffalse" and is_const(ins.a):
            if parse_const(ins.a) != 0:
                _note(log, "Constant condition", f"{ins}   →   (removed: condition is always true)")
                continue
            new = TAC("goto", None, None, ins.res)
            _note(log, "Constant condition", f"{ins}   →   {new}  (condition is always false)")
            ins = new

        # 4) remember constants known inside this basic block
        if ins.op == "=":
            if is_const(ins.a):
                t = var_types.get(ins.res)
                if t == "float":
                    ins = replace(ins, a=fmt_const(float(parse_const(ins.a))))
                elif t == "int":
                    ins = replace(ins, a=fmt_const(int(parse_const(ins.a))))
                consts[ins.res] = ins.a
            else:
                consts.pop(ins.res, None)
        elif ins.op in DEFINING:
            consts.pop(ins.res, None)

        out.append(ins)
    return out


def _eliminate_temps(code, log):
    """$t1 = a + b ; x = $t1   ==>   x = a + b   (when $t1 is used only once)."""
    uses = Counter()
    for ins in code:
        for v in (ins.a, ins.b):
            if v is not None:
                uses[v] += 1
    out, i = [], 0
    while i < len(code):
        ins = code[i]
        if (i + 1 < len(code) and ins.op in DEFINING and is_temp(ins.res)
                and uses[ins.res] == 1):
            nxt = code[i + 1]
            if nxt.op == "=" and nxt.a == ins.res:
                merged = replace(ins, res=nxt.res)
                _note(log, "Temporary elimination", f"{ins}  ;  {nxt}   →   {merged}")
                out.append(merged)
                i += 2
                continue
        out.append(ins)
        i += 1
    return out


def _remove_dead_temps(code, log):
    changed = True
    while changed:
        changed = False
        used = set()
        for ins in code:
            for v in (ins.a, ins.b):
                if v is not None:
                    used.add(v)
        new = []
        for ins in code:
            if ins.op in DEFINING and is_temp(ins.res) and ins.res not in used:
                _note(log, "Dead code elimination", f"{ins}   →   (removed: {ins.res} is never used)")
                changed = True
                continue
            new.append(ins)
        code = new
    return code


def _remove_unused_labels(code, log):
    targets = {i.res for i in code if i.op in ("goto", "iffalse")}
    out = []
    for ins in code:
        if ins.op == "label" and ins.res not in targets:
            _note(log, "Unused label removal", f"{ins}   →   (removed: nobody jumps here)")
            continue
        out.append(ins)
    return out


def _remove_unreachable(code, log):
    out, dead = [], False
    for ins in code:
        if ins.op == "label":
            dead = False
            out.append(ins)
            continue
        if dead:
            _note(log, "Unreachable code removal", f"{ins}   →   (removed: can never execute)")
            continue
        out.append(ins)
        if ins.op == "goto":
            dead = True
    return out


def _remove_jump_to_next(code, log):
    out = []
    for idx, ins in enumerate(code):
        if ins.op in ("goto", "iffalse"):
            j, following = idx + 1, set()
            while j < len(code) and code[j].op == "label":
                following.add(code[j].res)
                j += 1
            if ins.res in following:
                _note(log, "Jump-to-next removal", f"{ins}   →   (removed: jumps to the next instruction)")
                continue
        out.append(ins)
    return out


def optimize(code, var_types):
    """Return (optimized_code, log)."""
    log = []
    cur = [replace(i) for i in code]
    for _ in range(10):
        before = [str(i) for i in cur]
        cur = _fold_and_propagate(cur, var_types, log)
        cur = _eliminate_temps(cur, log)
        cur = _remove_dead_temps(cur, log)
        cur = _remove_unused_labels(cur, log)
        cur = _remove_unreachable(cur, log)
        cur = _remove_jump_to_next(cur, log)
        if [str(i) for i in cur] == before:
            break
    return cur, log
