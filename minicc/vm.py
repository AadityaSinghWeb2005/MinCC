"""Execution: a tiny virtual machine that interprets Three Address Code."""
from __future__ import annotations

from .ops import BINARY_OPS, eval_binop, eval_unop, fmt_value, is_const, parse_const


def run_tac(code, var_types, max_steps=20000, trace_limit=300):
    labels = {ins.res: i for i, ins in enumerate(code) if ins.op == "label"}
    env = {v: (0.0 if t == "float" else 0) for v, t in var_types.items()}
    output, trace = [], []
    pc, steps, error = 0, 0, None

    def val(x):
        if x in env:
            return env[x]
        if is_const(x):
            return parse_const(x)
        raise NameError(f"'{x}' has no value")

    def assign(name, v):
        t = var_types.get(name)
        if t == "int":
            v = int(v)
        elif t == "float":
            v = float(v)
        env[name] = v
        return v

    while pc < len(code):
        ins = code[pc]
        if ins.op == "label":
            pc += 1
            continue
        if steps >= max_steps:
            error = f"Execution stopped: step limit ({max_steps}) reached - possible infinite loop."
            break
        steps += 1
        next_pc, effect = pc + 1, ""
        try:
            op = ins.op
            if op == "=":
                effect = f"{ins.res} ← {fmt_value(assign(ins.res, val(ins.a)))}"
            elif op in BINARY_OPS:
                v = assign(ins.res, eval_binop(op, val(ins.a), val(ins.b)))
                effect = f"{ins.res} ← {fmt_value(v)}"
            elif op in ("neg", "not"):
                v = assign(ins.res, eval_unop(op, val(ins.a)))
                effect = f"{ins.res} ← {fmt_value(v)}"
            elif op == "print":
                text = fmt_value(val(ins.a))
                output.append(text)
                effect = f"output: {text}"
            elif op == "goto":
                next_pc = labels[ins.res]
                effect = f"jump to {ins.res}"
            elif op == "iffalse":
                if val(ins.a) == 0:
                    next_pc = labels[ins.res]
                    effect = f"condition false → jump to {ins.res}"
                else:
                    effect = "condition true → continue"
        except Exception as e:  # runtime error (e.g. division by zero)
            error = f"Runtime error in '{ins}': {e}"
            break
        if len(trace) < trace_limit:
            trace.append({"Step": steps, "Instruction": str(ins), "Effect": effect})
        pc = next_pc

    variables = {k: fmt_value(env[k]) for k in var_types}
    return {"output": output, "variables": variables, "steps": steps,
            "trace": trace, "error": error, "trace_truncated": steps > trace_limit}
