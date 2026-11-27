"""Phase 4 - Intermediate Code Generation: Three Address Code (TAC)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TAC:
    op: str
    a: Optional[str] = None
    b: Optional[str] = None
    res: Optional[str] = None

    def __str__(self):
        op = self.op
        if op == "=":
            return f"{self.res} = {self.a}"
        if op == "label":
            return f"{self.res}:"
        if op == "goto":
            return f"goto {self.res}"
        if op == "iffalse":
            return f"ifFalse {self.a} goto {self.res}"
        if op == "print":
            return f"print {self.a}"
        if op == "neg":
            return f"{self.res} = -{self.a}"
        if op == "not":
            return f"{self.res} = !{self.a}"
        return f"{self.res} = {self.a} {op} {self.b}"


class TACGenerator:
    def __init__(self):
        self.code = []
        self.tcount = 0
        self.lcount = 0

    def new_temp(self):
        self.tcount += 1
        return f"$t{self.tcount}"

    def new_label(self):
        self.lcount += 1
        return f"L{self.lcount}"

    def emit(self, op, a=None, b=None, res=None):
        self.code.append(TAC(op, a, b, res))

    def generate(self, root):
        self.stmt(root)
        return self.code

    def stmt(self, n):
        k = n.kind
        if k in ("Program", "Block"):
            for c in n.children:
                self.stmt(c)
        elif k == "Decl":
            if n.children:
                v = self.expr(n.children[0])
                self.emit("=", v, None, n.uid)
        elif k == "Assign":
            v = self.expr(n.children[0])
            self.emit("=", v, None, n.uid)
        elif k == "Print":
            v = self.expr(n.children[0])
            self.emit("print", v)
        elif k == "If":
            cond = self.expr(n.children[0])
            l_else = self.new_label()
            self.emit("iffalse", cond, None, l_else)
            self.stmt(n.children[1])
            if len(n.children) > 2:
                l_end = self.new_label()
                self.emit("goto", None, None, l_end)
                self.emit("label", None, None, l_else)
                self.stmt(n.children[2])
                self.emit("label", None, None, l_end)
            else:
                self.emit("label", None, None, l_else)
        elif k == "While":
            l_start, l_end = self.new_label(), self.new_label()
            self.emit("label", None, None, l_start)
            cond = self.expr(n.children[0])
            self.emit("iffalse", cond, None, l_end)
            self.stmt(n.children[1])
            self.emit("goto", None, None, l_start)
            self.emit("label", None, None, l_end)

    def expr(self, n):
        k = n.kind
        if k == "Num":
            return repr(n.value)
        if k == "Var":
            return n.uid
        if k == "UnOp":
            v = self.expr(n.children[0])
            t = self.new_temp()
            self.emit("neg" if n.value == "-" else "not", v, None, t)
            return t
        # BinOp
        l = self.expr(n.children[0])
        r = self.expr(n.children[1])
        t = self.new_temp()
        self.emit(n.value, l, r, t)
        return t
