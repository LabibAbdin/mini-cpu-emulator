# Mini CPU Emulator

A small CPU emulator and two-pass assembler written in Python. It runs programs written in a simple
**RISC-style assembly language** on a simulated 32-bit CPU with registers, memory and condition flags.
The syntax is similar to Arm assembly.

I built it to learn how a processor actually runs code: how instructions are fetched, decoded and executed,
how comparisons and branches create loops, and how an assembler turns text into something a CPU can run.

```
$ python main.py programs/factorial.asm --trace
   1 | MOV R0, #1             | R0=1    R1=0    ... | Z=0 N=0 | PC=1
   2 | MOV R1, #5             | R0=1    R1=5    ... | Z=0 N=0 | PC=2
   ...
  30 | HALT                   | R0=120  R1=0    ... | Z=0 N=1 | PC=8

Halted after 30 instructions.
Registers:
  R0 = 120
```

## Features

- **Simulated CPU**: 8 general-purpose 32-bit registers (`R0`–`R7`), a program counter, 256 words of memory,
  and Zero/Negative condition flags
- **Fetch-decode-execute cycle**, one instruction per step
- **Two-pass assembler** with labels (including forward references), comments, hex/negative immediates and
  a `.data` directive for putting values into memory
- **32-bit wraparound arithmetic**, like real hardware (`0x7FFFFFFF + 1` becomes `-2147483648`)
- **Trace mode** (`--trace`) that prints every register, flag and the PC after each instruction
- **Clear error messages with line numbers** for syntax errors, bad registers, undefined labels,
  out-of-range memory access, a missing `HALT`, and infinite loops (via a step limit)
- **30 unit tests**, covering every instruction, the error cases and the example programs
- No dependencies, just the Python standard library

## Instruction set

| Instruction | Example | Meaning |
|---|---|---|
| `MOV Rd, Rs/#imm` | `MOV R0, #5` | `R0 = 5` |
| `ADD Rd, Rn, Rm/#imm` | `ADD R0, R1, R2` | `R0 = R1 + R2` |
| `SUB Rd, Rn, Rm/#imm` | `SUB R1, R1, #1` | `R1 = R1 - 1` |
| `MUL Rd, Rn, Rm/#imm` | `MUL R0, R0, R1` | `R0 = R0 * R1` |
| `CMP Rn, Rm/#imm` | `CMP R1, #0` | Work out `R1 - 0` and set the flags (result is discarded) |
| `LDR Rd, [Rn, #off]` | `LDR R3, [R1]` | `R3 = memory[R1 + off]` |
| `STR Rd, [Rn, #off]` | `STR R0, [R2, #4]` | `memory[R2 + 4] = R0` |
| `B label` | `B loop` | Always jump |
| `BEQ label` | `BEQ done` | Jump if equal (Z = 1) |
| `BNE label` | `BNE loop` | Jump if not equal (Z = 0) |
| `BLT label` | `BLT done` | Jump if less than (N = 1) |
| `BGT label` | `BGT bigger` | Jump if greater than (Z = 0 and N = 0) |
| `HALT` | `HALT` | Stop the CPU |

Other syntax:
- `label:` marks a position you can branch to
- `; comment` runs to the end of the line
- `.data 100: 4, 8, 15` stores 4, 8 and 15 at memory addresses 100, 101 and 102

## How it works

```
 source.asm ──► Assembler ──► Program ──► CPU
                (2 passes)    (list of     ┌──────────────────────────────┐
                              instructions,│  FETCH   instr = program[PC] │
                              labels,      │          PC = PC + 1         │
                              data)        │  DECODE  look up the opcode  │
                                           │  EXECUTE update regs/memory/ │
                                           │          flags/PC            │
                                           └───── repeat until HALT ──────┘
```

**Assembler (`assembler.py`)**
1. *Pass 1* goes through the source, removes comments, and records each label's instruction index
   (and any `.data` values).
2. *Pass 2* parses each instruction into an opcode and typed operands (`("reg", 1)`, `("imm", 5)`,
   `("mem", base, offset)`, `("label", address)`). It checks them against a syntax table and replaces label names
   with addresses.

  Two passes are needed because a branch can jump forward to a label that hasn't been defined yet.

**CPU (`cpu.py`)**
- `step()` runs one fetch-decode-execute cycle. The PC is incremented *before* the instruction runs,
  so a branch only has to overwrite it.
- Decoding uses a lookup table from opcode to handler method, so adding an instruction means
  adding one entry and one method.
- `CMP` sets the flags and conditional branches read them. This is how Arm handles `if` statements and loops.

## Usage

Requires Python 3.8+.

```bash
python main.py programs/factorial.asm               # 5! = 120 in R0
python main.py programs/factorial.asm --trace       # step-by-step trace
python main.py programs/fibonacci.asm --memory 0 9  # first 10 Fibonacci numbers in memory
python main.py programs/array_stats.asm             # sum (R0) and max (R1) of an array
```

Run the tests:

```bash
python -m unittest discover -s tests -t . -v
```

## Project structure

```
├── assembler.py        # two-pass assembler: text → Program
├── cpu.py              # CPU state and fetch-decode-execute loop
├── main.py             # command-line interface
├── programs/           # example assembly programs
│   ├── factorial.asm
│   ├── fibonacci.asm
│   └── array_stats.asm
└── tests/              # unit tests (unittest)
```

## Design decisions

- **Word-addressed memory**: each address holds one 32-bit value, which keeps loads and stores simple.
  Real Arm is byte-addressed, so arrays step by 4.
- **Only `CMP` sets flags**: Arm's `ADD`/`SUB` only set flags with an `S` suffix (`ADDS`, `SUBS`). Leaving that out
  keeps the instruction set small.
- **Instructions stay as Python objects** instead of being encoded into 32-bit machine words. This keeps the
  focus on how instructions execute. Encoding is the next item below.

## Future improvements

- Encode instructions as 32-bit binary machine code and decode them with bit masks
- `BL`/`BX` instructions and a stack, for function calls
- More flags (Carry, Overflow) and the `S` suffix on arithmetic instructions
- A cycle-count model or a simple pipeline simulation (with hazards)
- A cache simulator in front of memory to measure hit/miss rates
