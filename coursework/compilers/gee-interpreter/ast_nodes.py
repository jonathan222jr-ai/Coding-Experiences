class Program:
    def __init__(self, functions):
        self.functions = functions

class FunctionDecl:
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class Block:
    def __init__(self, statements):
        self.statements = statements

class VarDecl:
    def __init__(self, name, init):
        self.name = name
        self.init = init

class Assign:
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

class If:
    def __init__(self, cond, then_branch, else_branch):
        self.cond = cond
        self.then_branch = then_branch
        self.else_branch = else_branch

class While:
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class Return:
    def __init__(self, expr):
        self.expr = expr

class Print:
    def __init__(self, expr):
        self.expr = expr

# Expressions
class IntLiteral:
    def __init__(self, value):
        self.value = value

class Var:
    def __init__(self, name):
        self.name = name

class BinOp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Call:
    def __init__(self, func, args):
        self.func = func
        self.args = args
