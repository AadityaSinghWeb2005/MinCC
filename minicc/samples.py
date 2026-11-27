"""Example programs and grammar text shown in the UI."""

SAMPLES = {
    "1. Arithmetic + Constant Folding": """// Constant folding demo
int a = 2 + 3 * 4;
int b = a * 1;
float c = 10 / 4.0;
int d = 10 / 4;
print(a);
print(b);
print(c);
print(d);
""",
    "2. If / Else + Dead Branch Removal": """int x = 10;
int y = 20;
if (x < y) {
    print(x);
} else {
    print(y);
}
int big = 0;
if (1 < 2) {
    big = 100;
} else {
    big = 200;
}
print(big);
""",
    "3. While Loop (Factorial)": """int n = 5;
int fact = 1;
int i = 1;
while (i <= n) {
    fact = fact * i;
    i = i + 1;
}
print(fact);
""",
    "4. Fibonacci Series": """int n = 10;
int a = 0;
int b = 1;
int i = 0;
while (i < n) {
    print(a);
    int temp = a + b;
    a = b;
    b = temp;
    i = i + 1;
}
""",
    "5. Block Scope (Symbol Table demo)": """int x = 1;
{
    int x = 2;
    print(x);
}
print(x);
""",
    "6. Lexical Error": """int a = 5 @ 3;
print(a);
""",
    "7. Syntax Error": """int a = 5
int b = 3;
print(a + b);
""",
    "8. Semantic Errors": """int a = 5;
float b = 2.5;
int c = a + undefinedVar;
int a = 10;
c = b % 2;
print(a / 0);
""",
}

GRAMMAR = """program      → statement* EOF
statement    → declaration | assignment | ifStmt | whileStmt | printStmt | block
declaration  → ( "int" | "float" ) IDENTIFIER ( "=" expression )? ";"
assignment   → IDENTIFIER "=" expression ";"
ifStmt       → "if" "(" expression ")" statement ( "else" statement )?
whileStmt    → "while" "(" expression ")" statement
printStmt    → "print" "(" expression ")" ";"
block        → "{" statement* "}"

expression   → logic_or
logic_or     → logic_and ( "||" logic_and )*
logic_and    → equality ( "&&" equality )*
equality     → relational ( ( "==" | "!=" ) relational )*
relational   → additive ( ( "<" | ">" | "<=" | ">=" ) additive )*
additive     → term ( ( "+" | "-" ) term )*
term         → unary ( ( "*" | "/" | "%" ) unary )*
unary        → ( "-" | "!" ) unary | primary
primary      → INTEGER | FLOAT | IDENTIFIER | "(" expression ")"
"""

TOKEN_TABLE = [
    {"Token Type": "KEYWORD", "Pattern": "int | float | if | else | while | print"},
    {"Token Type": "IDENTIFIER", "Pattern": "[A-Za-z_][A-Za-z_0-9]*"},
    {"Token Type": "INTEGER", "Pattern": "[0-9]+"},
    {"Token Type": "FLOAT", "Pattern": "[0-9]+\\.[0-9]+"},
    {"Token Type": "OPERATOR", "Pattern": "+ - * / % < > <= >= == != && || ! ="},
    {"Token Type": "SEPARATOR", "Pattern": "( ) { } ;"},
    {"Token Type": "COMMENT (ignored)", "Pattern": "// ... end of line"},
]
