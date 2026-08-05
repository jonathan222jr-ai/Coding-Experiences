import io
import contextlib

from ast_nodes import *
from lowering import Lowerer
from interpreter import IRInterpreter


def run_program(program):
    ir_prog = Lowerer().lower_program(program)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = IRInterpreter(ir_prog).run()
    output = buf.getvalue().strip().splitlines()
    return output, result


# -------------------------------------------------
# Test 1 (10 pts): constant return and print
# -------------------------------------------------
def test_01_constant_print_and_return():
    program = Program([
        FunctionDecl("main", [], Block([
            VarDecl("x", IntLiteral(42)),
            Print(Var("x")),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["42"]
    assert result == 0


# -------------------------------------------------
# Test 2 (10 pts): nested arithmetic expression
# -------------------------------------------------
def test_02_nested_arithmetic():
    program = Program([
        FunctionDecl("main", [], Block([
            VarDecl("x", BinOp(
                BinOp(IntLiteral(2), "+", IntLiteral(3)),
                "*",
                BinOp(IntLiteral(4), "-", IntLiteral(1))
            )),
            Print(Var("x")),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["15"]
    assert result == 0


# -------------------------------------------------
# Test 3 (10 pts): assignment after declaration
# -------------------------------------------------
def test_03_assignment():
    program = Program([
        FunctionDecl("main", [], Block([
            VarDecl("x", IntLiteral(5)),
            Assign("x", BinOp(Var("x"), "+", IntLiteral(7))),
            Print(Var("x")),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["12"]
    assert result == 0


# -------------------------------------------------
# Test 4 (10 pts): if/else true branch
# -------------------------------------------------
def test_04_if_true_branch():
    program = Program([
        FunctionDecl("main", [], Block([
            If(
                BinOp(IntLiteral(3), "<", IntLiteral(5)),
                Block([Print(IntLiteral(1))]),
                Block([Print(IntLiteral(2))])
            ),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["1"]
    assert result == 0


# -------------------------------------------------
# Test 5 (10 pts): if/else false branch
# -------------------------------------------------
def test_05_if_false_branch():
    program = Program([
        FunctionDecl("main", [], Block([
            If(
                BinOp(IntLiteral(8), "<", IntLiteral(2)),
                Block([Print(IntLiteral(111))]),
                Block([Print(IntLiteral(222))])
            ),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["222"]
    assert result == 0


# -------------------------------------------------
# Test 6 (10 pts): while loop multiple iterations
# -------------------------------------------------
def test_06_while_multiple_iterations():
    program = Program([
        FunctionDecl("main", [], Block([
            VarDecl("i", IntLiteral(0)),
            While(
                BinOp(Var("i"), "<", IntLiteral(3)),
                Block([
                    Print(Var("i")),
                    Assign("i", BinOp(Var("i"), "+", IntLiteral(1)))
                ])
            ),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["0", "1", "2"]
    assert result == 0


# -------------------------------------------------
# Test 7 (10 pts): while loop zero iterations
# -------------------------------------------------
def test_07_while_zero_iterations():
    program = Program([
        FunctionDecl("main", [], Block([
            VarDecl("i", IntLiteral(5)),
            While(
                BinOp(Var("i"), "<", IntLiteral(3)),
                Block([
                    Print(Var("i")),
                    Assign("i", BinOp(Var("i"), "+", IntLiteral(1)))
                ])
            ),
            Print(IntLiteral(99)),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["99"]
    assert result == 0


# -------------------------------------------------
# Test 8 (10 pts): function call with arguments
# -------------------------------------------------
def test_08_function_call_with_args():
    program = Program([
        FunctionDecl("add", ["a", "b"], Block([
            Return(BinOp(Var("a"), "+", Var("b")))
        ])),
        FunctionDecl("main", [], Block([
            VarDecl("x", Call("add", [IntLiteral(4), IntLiteral(5)])),
            Print(Var("x")),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["9"]
    assert result == 0


# -------------------------------------------------
# Test 9 (10 pts): nested function calls in expression
# -------------------------------------------------
def test_09_nested_calls_in_expression():
    program = Program([
        FunctionDecl("inc", ["x"], Block([
            Return(BinOp(Var("x"), "+", IntLiteral(1)))
        ])),
        FunctionDecl("main", [], Block([
            VarDecl("y", BinOp(
                Call("inc", [IntLiteral(10)]),
                "+",
                Call("inc", [IntLiteral(20)])
            )),
            Print(Var("y")),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["32"]
    assert result == 0


# -------------------------------------------------
# Test 10 (10 pts): recursion
# -------------------------------------------------
def test_10_recursion_factorial():
    program = Program([
        FunctionDecl("fact", ["n"], Block([
            If(
                BinOp(Var("n"), "<=", IntLiteral(1)),
                Block([
                    Return(IntLiteral(1))
                ]),
                Block([
                    Return(
                        BinOp(
                            Var("n"),
                            "*",
                            Call("fact", [BinOp(Var("n"), "-", IntLiteral(1))])
                        )
                    )
                ])
            )
        ])),
        FunctionDecl("main", [], Block([
            VarDecl("x", Call("fact", [IntLiteral(5)])),
            Print(Var("x")),
            Return(IntLiteral(0))
        ]))
    ])
    output, result = run_program(program)
    assert output == ["120"]
    assert result == 0
