"""Command-line entry point: python main.py programs/factorial.asm [--trace]"""

import argparse
import sys

from assembler import AssemblyError, assemble
from cpu import CPU, CPUError


def main():
    parser = argparse.ArgumentParser(description="Run an assembly program on the mini CPU emulator.")
    parser.add_argument("file", help="path to a .asm source file")
    parser.add_argument("--trace", action="store_true", help="print CPU state after every instruction")
    parser.add_argument("--memory", type=int, nargs=2, metavar=("START", "END"),
                        help="print memory words from START to END (inclusive)")
    parser.add_argument("--max-steps", type=int, default=100_000,
                        help="stop after this many instructions (default: 100000)")
    args = parser.parse_args()

    try:
        with open(args.file) as f:
            program = assemble(f.read())
        cpu = CPU(program, max_steps=args.max_steps)
        cpu.run(trace=args.trace)
    except OSError as error:
        sys.exit(f"Error: cannot read {args.file}: {error}")
    except (AssemblyError, CPUError) as error:
        sys.exit(f"Error: {error}")

    print(f"\nHalted after {cpu.steps} instructions.")
    print("Registers:")
    for i, value in enumerate(cpu.registers):
        print(f"  R{i} = {value}")
    print(f"Flags: Z={int(cpu.z_flag)} N={int(cpu.n_flag)}")

    if args.memory:
        start, end = max(args.memory[0], 0), min(args.memory[1], len(cpu.memory) - 1)
        print(f"Memory [{start}..{end}]:")
        for address in range(start, end + 1):
            print(f"  [{address}] = {cpu.memory[address]}")


if __name__ == "__main__":
    main()
