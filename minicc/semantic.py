"""Phase 3 - Semantic Analysis: symbol table, scope and type checking."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SemanticResult:
    errors: list = field(default_factory=list)      # (line, message)
    warnings: list = field(default_factory=list)    # (line, message)
    symbols: list = field(default_factory=list)     # symbol table rows
    var_types: dict = field(default_factory=dict)   # unique id -> "int"/"float"


class SemanticAnalyzer:
    def __init__(self):
        self.scopes = [{}]
        self.symbols = []
        self.errors = []
        self.warnings = []
        self.decl_count = {}
        self.var_types = {}
        self.warned = set()

    # ---- utilities -----------------------------------------------------
    def error(self, line, msg):
        self.errors.append((line, msg))

    def warn(self, line, msg):
        self.warnings.append((line, msg))

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def analyze(self, root):
        self.visit(root)
        return SemanticResult(self.errors, self.warnings, self.symbols, self.var_types)

    # ---- statements ----------------------------------------------------
    def visit(self, node):
        k = node.kind
        if k == "Program":
            for c in node.children:
                self.visit(c)
        elif k == "Block":
            self.scopes.append({})
            for c in node.children:
                self.visit(c)
            self.scopes.pop()
        elif k == "Decl":
            self.visit_decl(node)
        elif k == "Assign":
            self.visit_assign(node)
        elif k == "If":
            self.expr(node.children[0])
            self.visit(node.children[1])
            if len(node.children) > 2:
                self.visit(node.children[2])
        elif k == "While":
            self.expr(node.children[0])
            self.visit(node.children[1])
        elif k == "Print":
            self.expr(node.children[0])

    def visit_decl(self, node):
        vtype, name = node.value
        init_t = None
        if node.children:                       # analyse initializer BEFORE declaring
            init_t = self.expr(node.children[0])

        if name in self.scopes[-1]:
            self.error(node.line, f"Variable '{name}' is already declared in this scope")
            node.uid = self.scopes[-1][name]["Internal ID"]
            node.type = vtype
            return

        count = self.decl_count.get(name, 0)
        uid = name if count == 0 else f"{name}_{count}"
        self.decl_count[name] = count + 1

        depth = len(self.scopes) - 1
        row = {
            "Name": name,
            "Type": vtype,
            "Scope": "Global" if depth == 0 else f"Block (level {depth})",
            "Line": node.line,
            "Initialized at declaration": "Yes" if node.children else "No",
            "Times used": 0,
            "Internal ID": uid,
            "_assigned": bool(node.children),
        }
        self.scopes[-1][name] = row
        self.symbols.append(row)
        self.var_types[uid] = vtype
        node.uid, node.type = uid, vtype

        if init_t is not None:
            self.check_assign(vtype, init_t, node.line, name)

    def visit_assign(self, node):
        row = self.lookup(node.value)
        et = self.expr(node.children[0])
        if row is None:
            self.error(node.line, f"Variable '{node.value}' is used before declaration")
            return
        node.uid = row["Internal ID"]
        node.type = row["Type"]
        self.check_assign(row["Type"], et, node.line, node.value)
        row["_assigned"] = True

    def check_assign(self, target, source, line, name):
        if source == "error":
            return
        if target == "int" and source == "float":
            self.warn(line, f"Implicit conversion float -> int when assigning to '{name}' (value is truncated)")

    # ---- expressions ---------------------------------------------------
    def expr(self, node):
        k = node.kind
        t = "error"

        if k == "Num":
            t = "int" if isinstance(node.value, int) else "float"

        elif k == "Var":
            row = self.lookup(node.value)
            if row is None:
                self.error(node.line, f"Undeclared variable '{node.value}'")
            else:
                row["Times used"] += 1
                node.uid = row["Internal ID"]
                t = row["Type"]
                if not row["_assigned"] and node.uid not in self.warned:
                    self.warned.add(node.uid)
                    self.warn(node.line, f"Variable '{node.value}' may be used before it is assigned a value")

        elif k == "UnOp":
            ot = self.expr(node.children[0])
            if ot != "error":
                t = "int" if node.value == "!" else ot

        elif k == "BinOp":
            left, right = node.children
            lt, rt = self.expr(left), self.expr(right)
            op = node.value
            if op in ("/", "%") and right.kind == "Num" and right.value == 0:
                self.error(node.line, "Division by zero")
            if lt != "error" and rt != "error":
                if op in ("+", "-", "*", "/"):
                    t = "float" if "float" in (lt, rt) else "int"
                elif op == "%":
                    if "float" in (lt, rt):
                        self.error(node.line, "Operator '%' requires integer operands")
                    else:
                        t = "int"
                else:               # comparison / logical
                    t = "int"

        node.type = t
        return t
