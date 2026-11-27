"""Streamlit front-end for the MiniCC compiler demo.

Run with:   streamlit run app.py
"""
import pandas as pd
import streamlit as st

from minicc.pipeline import PHASES, compile_source
from minicc.samples import GRAMMAR, SAMPLES, TOKEN_TABLE
from minicc.visualizer import ast_to_dot, ast_to_text, pipeline_dot

st.set_page_config(page_title="MiniCC - Compiler Design Demo", page_icon="🛠️", layout="wide")

# ------------------------------------------------------------------ sidebar
sample_names = list(SAMPLES.keys())
if "source" not in st.session_state:
    st.session_state["source"] = SAMPLES[sample_names[0]]


def load_sample():
    st.session_state["source"] = SAMPLES[st.session_state["sample_choice"]]


with st.sidebar:
    st.header("⚙️ Controls")
    st.selectbox("Load an example program", sample_names, key="sample_choice", on_change=load_sample)
    max_steps = st.slider("Max execution steps (infinite-loop guard)", 100, 50000, 20000, step=100)
    st.markdown("---")
    st.subheader("Language supported")
    st.markdown(
        "- Types: `int`, `float`\n"
        "- Statements: declaration, assignment, `if / else`, `while`, `print()`, `{ blocks }`\n"
        "- Operators: `+ - * / %`, `< > <= >= == !=`, `&& || !`\n"
        "- Comments: `// ...`"
    )
    st.caption("Tip: after editing the code press **Ctrl + Enter** to compile.")

# --------------------------------------------------------------------- main
st.title("🛠️ MiniCC — A Mini Compiler Visualizer")
st.caption("Compiler Design Project · Python + Streamlit · Shows every phase of compilation live")

with st.expander("📌 Compiler pipeline overview", expanded=False):
    st.graphviz_chart(pipeline_dot())

source = st.text_area("✍️ Source code", key="source", height=300)

result = compile_source(source, max_steps=max_steps)

# ---- phase status bar
cols = st.columns(len(PHASES))
for col, phase in zip(cols, PHASES):
    status = result["status"][phase]
    with col:
        if status == "ok":
            st.success(f"✅ {phase}")
        elif status == "error":
            st.error(f"❌ {phase}")
        else:
            st.info(f"⏸ {phase}")

if result["internal_error"]:
    st.error(f"Internal compiler error: {result['internal_error']}")

tabs = st.tabs([
    "1️⃣ Lexical", "2️⃣ Syntax (AST)", "3️⃣ Semantic", "4️⃣ Intermediate Code",
    "5️⃣ Optimization", "6️⃣ Code Generation", "▶️ Execution", "📖 Grammar",
])

# ------------------------------------------------------------ 1. lexical
with tabs[0]:
    st.subheader("Lexical Analysis — source text → tokens")
    st.write("The scanner reads characters and groups them into **tokens** using regular expressions. "
             "Whitespace and comments are discarded.")
    for e in result["lex_errors"]:
        st.error(f"Lexical error at line {e.line}, column {e.col}: {e.message}")
    rows = [{"Line": t.line, "Column": t.col, "Token Type": t.type, "Lexeme": t.value}
            for t in result["tokens"] if t.type != "EOF"]
    if rows:
        df = pd.DataFrame(rows)
        c1, c2 = st.columns([3, 2])
        with c1:
            st.dataframe(df, hide_index=True)
        with c2:
            st.markdown("**Token count by type**")
            st.bar_chart(df["Token Type"].value_counts())
        st.metric("Total tokens", len(rows))
    else:
        st.info("No tokens found.")
    with st.expander("Token patterns (regular expressions)"):
        st.dataframe(pd.DataFrame(TOKEN_TABLE), hide_index=True)

# ------------------------------------------------------------- 2. syntax
with tabs[1]:
    st.subheader("Syntax Analysis — tokens → Abstract Syntax Tree")
    st.write("A **recursive-descent parser** checks the tokens against the grammar and builds an AST.")
    if result["parse_error"]:
        e = result["parse_error"]
        st.error(f"Syntax error at line {e.line}, column {e.col}: {e.message}")
    elif result["ast"] is None:
        st.info("Fix the lexical errors first.")
    else:
        show_types = st.checkbox("Show data types on expression nodes (from semantic analysis)", value=False)
        st.graphviz_chart(ast_to_dot(result["ast"], show_types))
        with st.expander("Text view of the AST"):
            st.code(ast_to_text(result["ast"]), language="text")

# ----------------------------------------------------------- 3. semantic
with tabs[2]:
    st.subheader("Semantic Analysis — symbol table, scopes & type checking")
    sem = result["sem"]
    if sem is None:
        st.info("Semantic analysis runs after the program is lexically and syntactically correct.")
    else:
        for line, msg in sem.errors:
            st.error(f"Semantic error at line {line}: {msg}")
        for line, msg in sem.warnings:
            st.warning(f"Warning at line {line}: {msg}")
        if not sem.errors:
            st.success("No semantic errors found.")
        st.markdown("**Symbol Table**")
        table = [{k: v for k, v in row.items() if not k.startswith("_")} for row in sem.symbols]
        if table:
            st.dataframe(pd.DataFrame(table), hide_index=True)
        else:
            st.info("No variables declared.")
        st.caption("Internal ID makes shadowed variables (same name in an inner block) unique.")

# ------------------------------------------------------------------ 4. TAC
with tabs[3]:
    st.subheader("Intermediate Code Generation — Three Address Code")
    if not result["tac"]:
        st.info("Available once the program has no lexical, syntax or semantic errors.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Three Address Code**")
            st.code("\n".join(f"{i + 1:>3}:  {ins}" for i, ins in enumerate(result["tac"])), language="text")
        with c2:
            st.markdown("**Quadruple representation**")
            quads = [{"#": i + 1, "Op": ins.op, "Arg1": ins.a or "", "Arg2": ins.b or "", "Result": ins.res or ""}
                     for i, ins in enumerate(result["tac"])]
            st.dataframe(pd.DataFrame(quads), hide_index=True)
        st.caption("`$t1, $t2, ...` are compiler-generated temporaries. `L1, L2, ...` are labels for jumps.")

# --------------------------------------------------------- 5. optimization
with tabs[4]:
    st.subheader("Code Optimization")
    if not result["tac"]:
        st.info("Available once the program compiles successfully.")
    else:
        before_n, after_n = len(result["tac"]), len(result["opt_tac"])
        m1, m2, m3 = st.columns(3)
        m1.metric("Instructions before", before_n)
        m2.metric("Instructions after", after_n, delta=after_n - before_n, delta_color="inverse")
        m3.metric("Optimizations applied", len(result["opt_log"]))
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Before optimization**")
            st.code("\n".join(str(i) for i in result["tac"]), language="text")
        with c2:
            st.markdown("**After optimization**")
            st.code("\n".join(str(i) for i in result["opt_tac"]) or "(empty program)", language="text")
        st.markdown("**What the optimizer did**")
        if result["opt_log"]:
            log_df = pd.DataFrame(result["opt_log"])
            log_df.insert(0, "#", range(1, len(log_df) + 1))
            st.dataframe(log_df, hide_index=True)
        else:
            st.info("Nothing to optimize in this program. Try example 1 or 2!")

# ----------------------------------------------------------- 6. codegen
with tabs[5]:
    st.subheader("Code Generation — optimized TAC → target assembly")
    if not result["asm"]:
        st.info("Available once the program compiles successfully.")
    else:
        st.code(result["asm"], language="text")
        st.caption("Target machine: 2 registers (R1, R2) and memory variables. "
                   "`#5` means the constant 5. Temporaries are kept in memory to keep the demo simple.")

# --------------------------------------------------------- 7. execution
with tabs[6]:
    st.subheader("Execution — run the compiled program")
    if result["run_opt"] is None:
        st.info("Available once the program compiles successfully.")
    else:
        ru, ro = result["run_unopt"], result["run_opt"]
        choice = st.radio("Show run of", ["Optimized code", "Unoptimized code"], horizontal=True)
        run = ro if choice == "Optimized code" else ru

        if run["error"]:
            st.error(run["error"])

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Program output**")
            st.code("\n".join(run["output"]) if run["output"] else "(no output)", language="text")
        with c2:
            st.markdown("**Final variable values**")
            vars_df = pd.DataFrame([{"Variable": k, "Value": v} for k, v in run["variables"].items()])
            if len(vars_df):
                st.dataframe(vars_df, hide_index=True)
            else:
                st.info("No variables.")

        m1, m2 = st.columns(2)
        m1.metric("Instructions executed (unoptimized)", ru["steps"])
        m2.metric("Instructions executed (optimized)", ro["steps"], delta=ro["steps"] - ru["steps"],
                  delta_color="inverse")
        if ru["output"] == ro["output"] and not ru["error"] and not ro["error"]:
            st.success("✔ The optimized program produces exactly the same output as the unoptimized one.")

        st.markdown("**Execution trace**")
        if run["trace"]:
            st.dataframe(pd.DataFrame(run["trace"]), hide_index=True)
            if run["trace_truncated"]:
                st.caption("Trace limited to the first 300 executed instructions.")

# ------------------------------------------------------------ 8. grammar
with tabs[7]:
    st.subheader("Grammar of the language (EBNF)")
    st.code(GRAMMAR, language="text")
    st.markdown(
        "**Operator precedence (high → low):** unary `- !` → `* / %` → `+ -` → relational → equality → `&&` → `||`"
    )
