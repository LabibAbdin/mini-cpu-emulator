import os
import unittest

from assembler import assemble
from cpu import CPU, CPUError

PROGRAMS_DIR = os.path.join(os.path.dirname(__file__), "..", "programs")


def run(source, **kwargs):
    cpu = CPU(assemble(source), **kwargs)
    cpu.run()
    return cpu


def run_file(name):
    with open(os.path.join(PROGRAMS_DIR, name)) as f:
        return run(f.read())


class TestInstructions(unittest.TestCase):
    def test_mov(self):
        cpu = run("MOV R0, #7\nMOV R1, R0\nHALT")
        self.assertEqual(cpu.registers[:2], [7, 7])

    def test_arithmetic(self):
        cpu = run("MOV R0, #6\nADD R1, R0, #4\nSUB R2, R0, #10\nMUL R3, R0, R0\nHALT")
        self.assertEqual(cpu.registers[1:4], [10, -4, 36])

    def test_cmp_sets_flags(self):
        cpu = run("MOV R0, #5\nCMP R0, #5\nHALT")
        self.assertTrue(cpu.z_flag)
        self.assertFalse(cpu.n_flag)

        cpu = run("MOV R0, #2\nCMP R0, #5\nHALT")
        self.assertFalse(cpu.z_flag)
        self.assertTrue(cpu.n_flag)

    def test_load_and_store(self):
        cpu = run("MOV R0, #99\nMOV R1, #20\nSTR R0, [R1, #3]\nLDR R2, [R1, #3]\nHALT")
        self.assertEqual(cpu.memory[23], 99)
        self.assertEqual(cpu.registers[2], 99)

    def test_data_directive_initialises_memory(self):
        cpu = run(".data 50: 11, 22\nLDR R0, [R1, #51]\nHALT")
        self.assertEqual(cpu.registers[0], 22)

    def test_branches(self):
        # Each branch should skip the MOV R0, #1 that follows it when taken.
        cases = {
            "BEQ": ("#5", True), "BNE": ("#5", False),
            "BLT": ("#9", True), "BGT": ("#1", True),
        }
        for branch, (value, taken) in cases.items():
            with self.subTest(branch=branch):
                cpu = run(f"MOV R1, #5\nCMP R1, {value}\n{branch} end\nMOV R0, #1\nend: HALT")
                self.assertEqual(cpu.registers[0], 0 if taken else 1)

    def test_32_bit_overflow_wraps(self):
        cpu = run("MOV R0, #0x7FFFFFFF\nADD R0, R0, #1\nHALT")
        self.assertEqual(cpu.registers[0], -(2 ** 31))

    def test_counts_steps(self):
        cpu = run("MOV R0, #1\nMOV R1, #2\nHALT")
        self.assertEqual(cpu.steps, 3)


class TestRuntimeErrors(unittest.TestCase):
    def test_infinite_loop_is_stopped(self):
        with self.assertRaises(CPUError):
            run("loop: B loop", max_steps=1000)

    def test_missing_halt(self):
        with self.assertRaisesRegex(CPUError, "missing HALT"):
            run("MOV R0, #1")

    def test_memory_out_of_range(self):
        with self.assertRaisesRegex(CPUError, "out of range"):
            run("MOV R0, #1000\nLDR R1, [R0]\nHALT")


class TestExamplePrograms(unittest.TestCase):
    def test_factorial(self):
        self.assertEqual(run_file("factorial.asm").registers[0], 120)

    def test_fibonacci(self):
        cpu = run_file("fibonacci.asm")
        self.assertEqual(cpu.memory[:10], [0, 1, 1, 2, 3, 5, 8, 13, 21, 34])

    def test_array_stats(self):
        cpu = run_file("array_stats.asm")
        self.assertEqual(cpu.registers[0], 108)  # sum
        self.assertEqual(cpu.registers[1], 42)   # max


if __name__ == "__main__":
    unittest.main()
