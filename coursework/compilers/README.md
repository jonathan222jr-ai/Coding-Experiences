# Compilers

Scanner, parser, and interpreter work — the front-to-back path from source text to
evaluated program, built up across a sequence of labs.

| Area | Contents |
|---|---|
| `Lab 1*`, `Lab01` | Lexical analysis — regular expressions and a hand-built scanner (Java, then C++) |
| `Lab 2`, `Lab_2` | LL(1) parsing with an explicit grammar (`grammarLL1.txt`) and a C++ parser |
| `Lab03`–`Lab08` | Successive front-end stages in C++, with Xcode projects and test files |
| `gee-parser` | Parser for the *gee* language in Python, with its grammar and `.gee` test programs |
| `gee-interpreter` | AST-walking interpreter for *gee* — `ast_nodes.py`, an IR (`ir.py`), a `lowering.py` pass, and `test_lab4.py` |

The `gee-*` directories are the most complete pieces here: together they take a *gee*
source file, parse it to an AST, lower it to an intermediate representation, and
execute it.

## Note on authorship

Some directories contain instructor-supplied scaffolding — notably
`A_partially_completed_scanner/` and the `all_tests/` and `testfiles/` fixtures. Those
were provided by the course; the implementation built on top of them is mine. They are
marked as vendored in `.gitattributes` so they don't skew the repository's language
statistics.
