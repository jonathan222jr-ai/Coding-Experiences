class IRProgram:
    def __init__(self, functions):
        self.functions = functions

class IRFunction:
    def __init__(self, name, params, instrs):
        self.name = name
        self.params = params
        self.instrs = instrs

# Instructions
class Const:
    def __init__(self, dst, value):
        self.dst = dst
        self.value = value

class Move:
    def __init__(self, dst, src):
        self.dst = dst
        self.src = src

class BinOp:
    def __init__(self, dst, op, a, b):
        self.dst = dst
        self.op = op
        self.a = a
        self.b = b

class Label:
    def __init__(self, name):
        self.name = name

class Jump:
    def __init__(self, label):
        self.label = label

class CJump:
    def __init__(self, cond, ltrue, lfalse):
        self.cond = cond
        self.ltrue = ltrue
        self.lfalse = lfalse

class Call:
    def __init__(self, dst, func, args):
        self.dst = dst
        self.func = func
        self.args = args

class Return:
    def __init__(self, value):
        self.value = value

class Print:
    def __init__(self, value):
        self.value = value
