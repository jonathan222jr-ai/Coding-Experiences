import argparse
from lowering import Lowerer
from interpreter import IRInterpreter
from examples import build_example

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump-ir", action="store_true")
    parser.add_argument("--run-ir", action="store_true")
    parser.add_argument("--trace-ir", action="store_true")
    args = parser.parse_args()

    program = build_example()
    lowerer = Lowerer()
    ir_prog = lowerer.lower_program(program)

    if args.dump_ir:
        for fn in ir_prog.functions:
            print(f"Function {fn.name}:")
            for instr in fn.instrs:
                print(vars(instr))

    if args.run_ir or args.trace_ir:
        interp = IRInterpreter(ir_prog)
        result = interp.run(trace=args.trace_ir)
        if not args.trace_ir:
            print(f"[program exited with {result}]")

if __name__ == "__main__":
    main()
