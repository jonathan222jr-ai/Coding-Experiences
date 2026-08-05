from ast_nodes import *

def build_example():
    return Program([
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
