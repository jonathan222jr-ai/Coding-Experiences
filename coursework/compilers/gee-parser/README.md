# Gee Parser — README

## Overview

`gee.py` is a recursive descent parser for **Gee**, a small structured programming language with Python-like indentation syntax. The parser reads a Gee source file, tokenizes it, builds an abstract syntax tree (AST), and prints the AST in a prefix-notation format.

---

## How It Works

### Stage 1: `mklines` — Preprocessing

Before any parsing occurs, `mklines` reads the source file line by line and transforms indentation into explicit structural tokens:

- Every line gets a `;` appended to mark its end.
- Comments (anything after `#`) are stripped.
- When indentation **increases**, an `@` is prepended to the line to signal a block open.
- When indentation **decreases**, one `~` is prepended per indent level closed, to signal block close(s).
- Trailing colons (e.g. from `if a > b:`) are preserved in the printed output but are handled gracefully by the parser.

The result is a flat string of annotated tokens passed to the `Lexer`.

### Stage 2: `Lexer` — Tokenization

The `Lexer` class uses a single regular expression (`lexRules`) to split the preprocessed text into a list of tokens. It supports:

- String and number literals
- Special characters: `( ) [ ] , : ; @ ~ $`
- Relational operators: `== != < <= > >=`
- Arithmetic operators: `+ - * /`
- Identifiers: `[a-zA-Z]\w*`

The lexer exposes `peek()` to look at the current token and `next()` to advance.

### Stage 3: Recursive Descent Parsing

The parser is a standard recursive descent parser with the following grammar levels (lowest to highest precedence):

```
parseStmtList  →  { parseStmt }
parseStmt      →  assignStmt | printStmt | ifStmt | whileStmt | exprStmt
ifStmt         →  'if' relExpr block [ 'else' block ]
whileStmt      →  'while' relExpr block
block          →  [ ':' ] ';' '@' { parseStmt } '~'
relExpr        →  addExpr [ relop addExpr ]
addExpr        →  term { ('+' | '-') term }
term           →  factor { ('*' | '/') factor }
factor         →  number | identifier | '(' addExpr ')'
```

### Stage 4: AST Output

Each AST node class implements `__str__` to produce prefix-notation output. Statements are printed one per line. `IfStmt` always emits `else` and `endif` as separate lines, even when no else branch exists.

---

## AST Node Classes

| Class | Description | Output Format |
|---|---|---|
| `BinaryExpr` | Arithmetic or relational binary operation | `op left right` |
| `Number` | Numeric literal | the number value |
| `Identifier` | Variable name | the name |
| `AssignStmt` | Variable assignment | `= name expr` |
| `PrintStmt` | Print statement | `print expr` |
| `IfStmt` | If/else conditional | `if cond` / body / `else` / elsebody / `endif` |
| `WhileStmt` | While loop | `while cond` / body / `endwhile` |
| `Block` | Sequence of statements | newline-joined statements |

---

## Changes Made

### 1. Added missing AST node classes

The original code only defined `BinaryExpr` and `Number`. The following classes were added to support all statement types:

- `Identifier` — for variable references
- `AssignStmt` — for `x = expr` statements
- `PrintStmt` — for `print expr` statements
- `IfStmt` — for `if`/`else` conditionals
- `WhileStmt` — for `while` loops
- `Block` — for indented blocks of statements

### 2. Implemented `parseStmt`

The original code called `parseStmt` but never defined it. The implementation dispatches on the leading token:

- `if` → parses condition and block, with optional `else` block
- `while` → parses condition and block
- `print` → parses expression and consumes `;`
- identifier followed by `=` → assignment statement
- anything else → bare expression statement

### 3. Implemented `relExpr`

Added a `relExpr` layer between `addExpr` and statement-level parsing to handle comparison operators (`==`, `!=`, `<`, `<=`, `>`, `>=`).

### 4. Implemented `parseBlock`

Added `parseBlock` to consume an `@`-delimited indented block as produced by `mklines`. It skips a leading `:` and `;` (left over from the header line of an `if`/`while`/`else`) before matching the `@` open token, then collects statements until `~` closes the block.

### 5. Fixed `parseStmtList`

The original had a broken indentation error (mixed tabs and spaces inside the `while` loop body) and returned only the last statement instead of accumulating all of them. Fixed to build and return a proper list.

### 6. Fixed `parse` to call `parseStmtList`

The original `parse` called `addExpr` directly, meaning only a single expression was ever parsed. Changed to call `parseStmtList` so the full program is parsed.

### 7. Fixed `IfStmt.__str__` output format

Changed to emit each part on its own line, and to always include `else` and `endif` regardless of whether an else branch exists:

```
if > a b
= ans a
else
= ans b
endif
```

### 8. Fixed `Block.__str__` separator

Changed from `" ".join(...)` (all on one line) to `"\n".join(...)` so each statement in a block prints on its own line.

### 9. Renamed `dict` to `symbol_table`

The original code used `dict = {}`, which shadows Python's built-in `dict` type. Renamed to `symbol_table`.

### 10. Set `debug = False`

The original had `debug = True`, which caused `Factor:`, `Term:`, and `addExpr:` trace lines to print for every token, cluttering the output. Set to `False` for clean output.

---

## Running

```bash
python gee.py <source_file>
```

### Example Output

For a `max3` program:

```
= ans b
if > a b
if > a c
= ans a
else
= ans b
endif
else
if < b c
= ans c
else
endif
endif
= max3 ans
```