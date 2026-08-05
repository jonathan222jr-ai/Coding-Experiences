Lab 4: Lowering to IR
Name: [Jonathan Ramirez]
Email: [Jramirez431]
Overview
This lab implements the lowering phase of a compiler pipeline. The goal was to translate a high-level Abstract Syntax Tree (AST) into a flat, low-level Intermediate Representation (IR) that can be executed by the provided IR interpreter.
What Was Implemented
The only file modified was lowering.py. The following four methods were implemented inside the Lowerer class:
lower_program
Iterates over all function declarations in the AST and calls lower_function on each one, returning a complete IRProgram.
lower_function
Resets the instruction list for each function so instructions don't bleed between functions. Calls lower_block on the function body and returns an IRFunction with the collected instructions.
lower_stmt
Handles each statement type by emitting the appropriate IR instructions:

VarDecl / Assign — lowers the right-hand expression to a temp, emits a Move into the variable name
If/Else — lowers the condition, emits a CJump to true/false labels, emits both branches with a Jump to a shared merge label at the end
While — emits a loop-top label, lowers the condition, emits a CJump to body or exit, emits the body, then jumps back to the loop-top label
Return — lowers the expression to a temp, emits a Return
Print — lowers the expression to a temp, emits a Print

lower_expr
Always returns the name of a temporary variable holding the result:

IntLiteral — allocates a fresh temp, emits a Const, returns the temp
Var — returns the variable name directly (no extra instruction needed)
BinOp — recursively lowers left and right operands, allocates a fresh temp, emits a BinOp instruction, returns the temp
Call — lowers each argument to a temp, allocates a fresh temp for the return value, emits a Call, returns the temp

Testing
All 10 provided grading tests in test_lab4.py pass successfully:
pytest test_lab4.py
# 10 passed
Tests cover: constant print/return, nested arithmetic, assignment, if/else true and false branches, while loops (multiple and zero iterations), function calls with arguments, nested function calls, and recursion (factorial of 5).