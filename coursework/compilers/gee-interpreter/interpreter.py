from ir import *

class IRInterpreter:
    def __init__(self, program):
        self.program = {f.name: f for f in program.functions}

    def run(self, entry="main", trace=False):
        return self.exec_function(entry, [], trace)

    def exec_function(self, name, args, trace):
        fn = self.program[name]
        env = dict(zip(fn.params, args))
        pc = 0
        instrs = fn.instrs
        labels = {instr.name: i for i, instr in enumerate(instrs) if isinstance(instr, Label)}

        def val(x):
            return env[x] if isinstance(x, str) else x

        while pc < len(instrs):
            instr = instrs[pc]
            if trace:
                print("TRACE:", instr.__class__.__name__, vars(instr))

            if isinstance(instr, Const):
                env[instr.dst] = instr.value
            elif isinstance(instr, Move):
                env[instr.dst] = val(instr.src)
            elif isinstance(instr, BinOp):
                a, b = val(instr.a), val(instr.b)
                if instr.op == "+": env[instr.dst] = a + b
                elif instr.op == "-": env[instr.dst] = a - b
                elif instr.op == "*": env[instr.dst] = a * b
                elif instr.op == "/": env[instr.dst] = a // b
                elif instr.op == "<": env[instr.dst] = int(a < b)
                elif instr.op == "<=": env[instr.dst] = int(a <= b)
                elif instr.op == ">": env[instr.dst] = int(a > b)
                elif instr.op == ">=": env[instr.dst] = int(a >= b)
                elif instr.op == "==": env[instr.dst] = int(a == b)
                elif instr.op == "!=": env[instr.dst] = int(a != b)
                else:
                    raise ValueError(f"Unsupported operator: {instr.op}")
            elif isinstance(instr, Jump):
                pc = labels[instr.label]
                continue
            elif isinstance(instr, CJump):
                pc = labels[instr.ltrue] if val(instr.cond) else labels[instr.lfalse]
                continue
            elif isinstance(instr, Call):
                env[instr.dst] = self.exec_function(instr.func, [val(a) for a in instr.args], trace)
            elif isinstance(instr, Return):
                return val(instr.value)
            elif isinstance(instr, Print):
                print(val(instr.value))
            elif isinstance(instr, Label):
                pass
            else:
                raise ValueError(f"Unsupported instruction: {instr}")
            pc += 1
        return 0
