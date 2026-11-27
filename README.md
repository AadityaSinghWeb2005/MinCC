# MiniCC – Mini Compiler Visualizer (Compiler Design Demo)

A working demo of **all phases of a compiler** for a small C-like language, with a live Streamlit UI.

## How to run
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open http://localhost:8501 (it opens automatically).

## Project structure
```
app.py                 Streamlit UI (tabs for each phase)
minicc/lexer.py        Phase 1  Lexical analysis   (regex scanner)
minicc/parser.py       Phase 2  Syntax analysis    (recursive descent -> AST)
minicc/semantic.py     Phase 3  Semantic analysis  (symbol table, scopes, type check)
minicc/tac.py          Phase 4  Intermediate code  (Three Address Code / quadruples)
minicc/optimizer.py    Phase 5  Optimization       (folding, propagation, dead code...)
minicc/assembly.py     Phase 6  Code generation    (assembly-like target code)
minicc/vm.py           Execution of the generated code (virtual machine + trace)
minicc/ops.py          Shared operator semantics
minicc/visualizer.py   Graphviz DOT generation for AST / pipeline
minicc/samples.py      Example programs + grammar
minicc/pipeline.py     Glue: runs all phases
```

## Suggested demo flow for the teacher (3-5 minutes)
1. Pick **"1. Arithmetic + Constant Folding"** -> show tokens, then the AST graph.
2. Open **Semantic** tab -> symbol table. Load **"5. Block Scope"** to show shadowing.
3. Open **Intermediate Code** -> TAC + quadruples.
4. Open **Optimization** -> before/after + log. Load **"2. If / Else"** to show dead-branch removal.
5. Open **Code Generation** -> assembly. Then **Execution** -> output + trace.
6. Load examples **6, 7, 8** to show lexical, syntax and semantic error detection.
7. Load **"3. While Loop (Factorial)"** and compare executed instructions before/after optimization.

## Language
```c
int a = 5;
float b = 2.5;
while (a > 0) { a = a - 1; }
if (a == 0) { print(b); } else { print(a); }
```
