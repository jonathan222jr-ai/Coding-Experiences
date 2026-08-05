from ir import *
import ast_nodes as ast


class Lowerer:
    def __init__(self):
        self.temp_counter = 0
        self.label_counter = 0
        self.current_instrs = []

    def fresh_temp(self):
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def fresh_label(self, prefix="L"):
        self.label_counter += 1
        return f"{prefix}{self.label_counter}"

    def emit(self, instr):
        self.current_instrs.append(instr)

    # =======================
    # Implementation
    # =======================

    def lower_program(self, program):
        functions = [self.lower_function(fn) for fn in program.functions]
        return IRProgram(functions)

    def lower_function(self, fn):
        self.current_instrs = []
        self.lower_block(fn.body)
        return IRFunction(fn.name, fn.params, self.current_instrs)

    def lower_block(self, block):
        for stmt in block.statements:
            self.lower_stmt(stmt)

    def lower_stmt(self, stmt):
        if isinstance(stmt, ast.VarDecl):
            t = self.lower_expr(stmt.init)
            self.emit(Move(stmt.name, t))

        elif isinstance(stmt, ast.Assign):
            t = self.lower_expr(stmt.expr)
            self.emit(Move(stmt.name, t))

        elif isinstance(stmt, ast.If):
            cond_t = self.lower_expr(stmt.cond)
            l_true  = self.fresh_label("Ltrue")
            l_false = self.fresh_label("Lfalse")
            l_end   = self.fresh_label("Lend")

            self.emit(CJump(cond_t, l_true, l_false))

            self.emit(Label(l_true))
            self.lower_block(stmt.then_branch)
            self.emit(Jump(l_end))

            self.emit(Label(l_false))
            if stmt.else_branch is not None:
                self.lower_block(stmt.else_branch)
            self.emit(Jump(l_end))

            self.emit(Label(l_end))

        elif isinstance(stmt, ast.While):
            l_top  = self.fresh_label("Lloop")
            l_body = self.fresh_label("Lbody")
            l_exit = self.fresh_label("Lexit")

            self.emit(Label(l_top))
            cond_t = self.lower_expr(stmt.cond)
            self.emit(CJump(cond_t, l_body, l_exit))

            self.emit(Label(l_body))
            self.lower_block(stmt.body)
            self.emit(Jump(l_top))

            self.emit(Label(l_exit))

        elif isinstance(stmt, ast.Return):
            t = self.lower_expr(stmt.expr)
            self.emit(Return(t))

        elif isinstance(stmt, ast.Print):
            t = self.lower_expr(stmt.expr)
            self.emit(Print(t))

        else:
            raise NotImplementedError(f"Unknown statement type: {type(stmt)}")

    def lower_expr(self, expr):
        if isinstance(expr, ast.IntLiteral):
            t = self.fresh_temp()
            self.emit(Const(t, expr.value))
            return t

        elif isinstance(expr, ast.Var):
            # Variable names are already valid src/dst — return directly
            return expr.name

        elif isinstance(expr, ast.BinOp):
            a = self.lower_expr(expr.left)
            b = self.lower_expr(expr.right)
            t = self.fresh_temp()
            self.emit(BinOp(t, expr.op, a, b))
            return t

        elif isinstance(expr, ast.Call):
            arg_temps = [self.lower_expr(arg) for arg in expr.args]
            t = self.fresh_temp()
            self.emit(Call(t, expr.func, arg_temps))
            return t

        else:
            raise NotImplementedError(f"Unknown expression type: {type(expr)}")