"""Runs every compiler phase and collects the results for the UI."""
from __future__ import annotations

from .assembly import generate_assembly
from .lexer import tokenize
from .optimizer import optimize
from .parser import ParseError, Parser
from .semantic import SemanticAnalyzer
from .tac import TACGenerator
from .vm import run_tac

PHASES = ["Lexical", "Syntax", "Semantic", "Intermediate Code", "Optimization", "Code Generation"]


def compile_source(source, max_steps=20000):
    r = {
        "status": {p: "skipped" for p in PHASES},
        "tokens": [], "lex_errors": [], "ast": None, "parse_error": None,
        "sem": None, "tac": [], "opt_tac": [], "opt_log": [], "asm": "",
        "run_unopt": None, "run_opt": None, "internal_error": None,
    }
    try:
        tokens, lex_errors = tokenize(source)
        r["tokens"], r["lex_errors"] = tokens, lex_errors
        if lex_errors:
            r["status"]["Lexical"] = "error"
            return r
        r["status"]["Lexical"] = "ok"

        try:
            ast = Parser(tokens).parse()
        except ParseError as e:
            r["parse_error"] = e
            r["status"]["Syntax"] = "error"
            return r
        r["ast"] = ast
        r["status"]["Syntax"] = "ok"

        sem = SemanticAnalyzer().analyze(ast)
        r["sem"] = sem
        if sem.errors:
            r["status"]["Semantic"] = "error"
            return r
        r["status"]["Semantic"] = "ok"

        tac = TACGenerator().generate(ast)
        r["tac"] = tac
        r["status"]["Intermediate Code"] = "ok"

        opt, log = optimize(tac, sem.var_types)
        r["opt_tac"], r["opt_log"] = opt, log
        r["status"]["Optimization"] = "ok"

        r["asm"] = generate_assembly(opt, sem.var_types)
        r["status"]["Code Generation"] = "ok"

        r["run_unopt"] = run_tac(tac, sem.var_types, max_steps)
        r["run_opt"] = run_tac(opt, sem.var_types, max_steps)
    except Exception as e:  # safety net so the demo never crashes
        r["internal_error"] = f"{type(e).__name__}: {e}"
    return r
