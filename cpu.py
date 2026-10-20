"""
A simple CPU that runs a Program produced by the assembler.

The CPU repeats one cycle until it hits HALT:
    1. FETCH   - read the instruction at the program counter (PC)
    2. DECODE  - work out which operation it is and what its operands are
    3. EXECUTE - do the operation (update registers, memory, flags or PC)
"""

from assembler import NUM_REGISTERS


class CPUError(Exception):
    """Raised when a program does something illegal at runtime."""


MEMORY_SIZE = 256  # number of memory words


def to_int32(value):
    """Wrap a Python int to a signed 32-bit value, like a real 32-bit register."""
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


# When each branch is taken, based on the flags set by the last CMP.
# Z (zero) = the two compared values were equal.
# N (negative) = the first value was less than the second.
BRANCH_CONDITIONS = {
    "B":   lambda z, n: True,
    "BEQ": lambda z, n: z,
    "BNE": lambda z, n: not z,
    "BLT": lambda z, n: n,
    "BGT": lambda z, n: not z and not n,
}


class CPU:
    def __init__(self, program, max_steps=100_000):
        self.program = program
        self.max_steps = max_steps  # protects against infinite loops

        self.registers = [0] * NUM_REGISTERS
        self.memory = [0] * MEMORY_SIZE
        self.pc = 0          # program counter: index of the next instruction
        self.z_flag = False  # zero flag
        self.n_flag = False  # negative flag
        self.halted = False
        self.steps = 0       # number of instructions executed

        for address, value in program.data.items():
            self._check_address(address)
            self.memory[address] = to_int32(value)

        # Decode table: maps each opcode to the method that executes it.
        self.handlers = {
            "MOV": self._mov,
            "ADD": self._alu,
            "SUB": self._alu,
            "MUL": self._alu,
            "CMP": self._cmp,
            "LDR": self._ldr,
            "STR": self._str,
            "HALT": self._halt,
        }
        for branch in BRANCH_CONDITIONS:
            self.handlers[branch] = self._branch

    # ---------------------------------------------------------------- running

    def run(self, trace=False):
        """Run until HALT. If trace is True, print the CPU state after every step."""
        while not self.halted:
            if self.steps >= self.max_steps:
                raise CPUError(f"stopped after {self.max_steps} steps (infinite loop?)")
            instruction = self.step()
            if trace:
                print(self.format_trace(instruction))

    def step(self):
        """Execute one instruction (one fetch-decode-execute cycle)."""
        if self.halted:
            raise CPUError("CPU is halted")
        if not 0 <= self.pc < len(self.program.instructions):
            raise CPUError(f"PC={self.pc} is outside the program (missing HALT?)")

        # FETCH
        instruction = self.program.instructions[self.pc]
        self.pc += 1  # point at the next instruction; branches may overwrite this

        # DECODE
        handler = self.handlers[instruction.op]

        # EXECUTE
        try:
            handler(instruction)
        except CPUError as error:
            raise CPUError(f"line {instruction.line} ({instruction.text}): {error}") from None

        self.steps += 1
        return instruction

    # ------------------------------------------------------------ instructions

    def _mov(self, instr):
        dest, src = instr.args
        self.registers[dest[1]] = to_int32(self._read(src))

    def _alu(self, instr):
        dest, a, b = instr.args
        x, y = self._read(a), self._read(b)
        if instr.op == "ADD":
            result = x + y
        elif instr.op == "SUB":
            result = x - y
        else:  # MUL
            result = x * y
        self.registers[dest[1]] = to_int32(result)

    def _cmp(self, instr):
        # CMP subtracts the operands but throws the result away; it only sets flags.
        result = to_int32(self._read(instr.args[0]) - self._read(instr.args[1]))
        self.z_flag = result == 0
        self.n_flag = result < 0

    def _ldr(self, instr):
        dest, mem = instr.args
        self.registers[dest[1]] = self.memory[self._address(mem)]

    def _str(self, instr):
        src, mem = instr.args
        self.memory[self._address(mem)] = self.registers[src[1]]

    def _branch(self, instr):
        if BRANCH_CONDITIONS[instr.op](self.z_flag, self.n_flag):
            self.pc = instr.args[0][1]

    def _halt(self, instr):
        self.halted = True

    # ---------------------------------------------------------------- helpers

    def _read(self, operand):
        """Get the value of a register or immediate operand."""
        kind, value = operand
        return self.registers[value] if kind == "reg" else value

    def _address(self, mem_operand):
        """Work out the memory address for [Rn] or [Rn, #offset]."""
        _, base, offset = mem_operand
        address = self.registers[base] + offset
        self._check_address(address)
        return address

    def _check_address(self, address):
        if not 0 <= address < MEMORY_SIZE:
            raise CPUError(f"memory address {address} out of range (0-{MEMORY_SIZE - 1})")

    def format_trace(self, instruction):
        regs = " ".join(f"R{i}={v:<4}" for i, v in enumerate(self.registers))
        flags = f"Z={int(self.z_flag)} N={int(self.n_flag)}"
        return f"{self.steps:>4} | {instruction.text:<22} | {regs} | {flags} | PC={self.pc}"
