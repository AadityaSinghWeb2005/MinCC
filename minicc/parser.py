"""Phase 2 - Syntax Analysis (Recursive Descent Parser) -> builds an AST."""
from __future__ import annotations


class Node:
    """Generic AST node."""

    def __init__(self, kind, value=None, children=None, line=0):
        self.kind = kind
        self.value = value
        self.children = children or []
        self.line = line
        self.type = None   # filled by semantic analysis
        self.uid = None    # unique variable id, filled by semantic analysis

    def label(self):
        if self.kind == "Decl":
            return f"Decl {self.value[0]} {self.value[1]}"
        if self.kind == "Assign":
            return f"Assign {self.value}"
        if self.kind in ("Num", "Var", "BinOp", "UnOp"):
            return str(self.value)
        return self.kind


class ParseError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col


LEVELS = [
    ("||",),
    ("&&",),
    ("==", "!="),
    ("<", ">", "<=", ">="),
    ("+", "-"),
    ("*", "/", "%"),
]


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    # ---- helpers -------------------------------------------------------
    def cur(self):
        return self.tokens[self.i]

    def advance(self):
        tok = self.tokens[self.i]
        if tok.type != "EOF":
            self.i += 1
        return tok

    def check(self, value):
        t = self.cur()
        return t.type in ("KEYWORD", "OPERATOR", "SEPARATOR") and t.value == value

    def describe(self, tok):
        return "end of file" if tok.type == "EOF" else f"'{tok.value}'"

    def expect(self, value):
        if self.check(value):
            return self.advance()
        t = self.cur()
        raise ParseError(f"Expected '{value}' but found {self.describe(t)}", t.line, t.col)

    def expect_identifier(self, what="a variable name"):
        t = self.cur()
        if t.type == "IDENTIFIER":
            return self.advance()
        raise ParseError(f"Expected {what} but found {self.describe(t)}", t.line, t.col)

    # ---- grammar -------------------------------------------------------
    def parse(self):
        stmts = []
        while self.cur().type != "EOF":
            stmts.append(self.statement())
        return Node("Program", None, stmts, 1)

    def block(self):
        start = self.expect("{")
        stmts = []
        while not self.check("}") and self.cur().type != "EOF":
            stmts.append(self.statement())
        self.expect("}")
        return Node("Block", None, stmts, start.line)

    def body(self):
        """A loop/if body: either a block or a single statement (wrapped in a Block)."""
        if self.check("{"):
            return self.block()
        stmt = self.statement()
        return Node("Block", None, [stmt], stmt.line)

    def statement(self):
        t = self.cur()

        if self.check("int") or self.check("float"):
            vtype = self.advance().value
            name = self.expect_identifier().value
            children = []
            if self.check("="):
                self.advance()
                children.append(self.expression())
            self.expect(";")
            return Node("Decl", (vtype, name), children, t.line)

        if self.check("if"):
            self.advance()
            self.expect("(")
            cond = self.expression()
            self.expect(")")
            then_b = self.body()
            children = [cond, then_b]
            if self.check("else"):
                self.advance()
                children.append(self.body())
            return Node("If", None, children, t.line)

        if self.check("while"):
            self.advance()
            self.expect("(")
            cond = self.expression()
            self.expect(")")
            return Node("While", None, [cond, self.body()], t.line)

        if self.check("print"):
            self.advance()
            self.expect("(")
            e = self.expression()
            self.expect(")")
            self.expect(";")
            return Node("Print", None, [e], t.line)

        if self.check("{"):
            return self.block()

        if t.type == "IDENTIFIER":
            name = self.advance().value
            self.expect("=")
            e = self.expression()
            self.expect(";")
            return Node("Assign", name, [e], t.line)

        raise ParseError(f"Unexpected token {self.describe(t)}", t.line, t.col)

    def expression(self):
        return self._level(0)

    def _level(self, k):
        if k == len(LEVELS):
            return self.unary()
        left = self._level(k + 1)
        while self.cur().type == "OPERATOR" and self.cur().value in LEVELS[k]:
            op = self.advance()
            right = self._level(k + 1)
            left = Node("BinOp", op.value, [left, right], op.line)
        return left

    def unary(self):
        t = self.cur()
        if t.type == "OPERATOR" and t.value in ("-", "!"):
            op = self.advance()
            return Node("UnOp", op.value, [self.unary()], op.line)
        return self.primary()

    def primary(self):
        t = self.cur()
        if t.type == "INTEGER":
            self.advance()
            return Node("Num", int(t.value), [], t.line)
        if t.type == "FLOAT":
            self.advance()
            return Node("Num", float(t.value), [], t.line)
        if t.type == "IDENTIFIER":
            self.advance()
            return Node("Var", t.value, [], t.line)
        if self.check("("):
            self.advance()
            e = self.expression()
            self.expect(")")
            return e
        raise ParseError(f"Expected an expression but found {self.describe(t)}", t.line, t.col)
