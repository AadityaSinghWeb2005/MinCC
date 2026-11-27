"""Helpers that turn the AST / pipeline into Graphviz DOT text (rendered by Streamlit)."""
from __future__ import annotations

EXPR_KINDS = {"Num", "Var", "BinOp", "UnOp"}
LEAF_KINDS = {"Num", "Var"}


def _esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def ast_to_dot(root, show_types=False):
    lines = [
        "digraph AST {",
        '  node [fontname="Helvetica", fontsize=11];',
        '  edge [color="#888888"];',
    ]
    counter = [0]

    def walk(node):
        nid = f"n{counter[0]}"
        counter[0] += 1
        label = _esc(node.label())
        if show_types and node.kind in EXPR_KINDS and node.type and node.type != "error":
            label += "\\n(" + node.type + ")"
        if node.kind == "Program":
            shape, color = "box", "#e6ccff"
        elif node.kind in LEAF_KINDS:
            shape, color = "ellipse", "#d9f2d9"
        elif node.kind in EXPR_KINDS:
            shape, color = "ellipse", "#fff2cc"
        else:
            shape, color = "box", "#cfe8ff"
        lines.append(f'  {nid} [label="{label}", shape={shape}, style="filled,rounded", fillcolor="{color}"];')
        for child in node.children:
            cid = walk(child)
            lines.append(f"  {nid} -> {cid};")
        return nid

    walk(root)
    lines.append("}")
    return "\n".join(lines)


def ast_to_text(node, indent=0):
    text = "  " * indent + node.label()
    if node.type and node.kind in EXPR_KINDS:
        text += f"   : {node.type}"
    out = [text]
    for c in node.children:
        out.append(ast_to_text(c, indent + 1))
    return "\n".join(out)


def pipeline_dot():
    return """
digraph Pipeline {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#e8f0fe", fontname="Helvetica", fontsize=11];
  edge [fontname="Helvetica", fontsize=9, color="#666666"];
  src [label="Source\\nCode", fillcolor="#fff2cc"];
  lex [label="1. Lexical\\nAnalyzer"];
  syn [label="2. Syntax\\nAnalyzer"];
  sem [label="3. Semantic\\nAnalyzer"];
  icg [label="4. Intermediate\\nCode Gen"];
  opt [label="5. Code\\nOptimizer"];
  cg  [label="6. Code\\nGenerator"];
  out [label="Target\\nCode + Run", fillcolor="#d9f2d9"];
  src -> lex; lex -> syn [label="tokens"]; syn -> sem [label="AST"];
  sem -> icg [label="annotated AST"]; icg -> opt [label="TAC"];
  opt -> cg [label="optimized TAC"]; cg -> out;
}
"""
