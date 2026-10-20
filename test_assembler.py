import unittest

from assembler import AssemblyError, assemble


class TestAssembler(unittest.TestCase):
    def test_parses_registers_and_immediates(self):
        program = assemble("ADD R1, R2, #5")
        instr = program.instructions[0]
        self.assertEqual(instr.op, "ADD")
        self.assertEqual(instr.args, [("reg", 1), ("reg", 2), ("imm", 5)])

    def test_ignores_comments_and_blank_lines(self):
        program = assemble("; a comment\n\n  MOV R0, #1 ; set R0\nHALT")
        self.assertEqual(len(program.instructions), 2)

    def test_resolves_forward_labels(self):
        # `done` is used before it is defined, which is why we need two passes
        program = assemble("B done\nMOV R0, #1\ndone: HALT")
        self.assertEqual(program.labels["done"], 2)
        self.assertEqual(program.instructions[0].args, [("label", 2)])

    def test_label_on_its_own_line(self):
        program = assemble("start:\n  HALT")
        self.assertEqual(program.labels["start"], 0)

    def test_label_starting_with_r_is_not_a_register(self):
        program = assemble("repeat: B repeat")
        self.assertEqual(program.instructions[0].args, [("label", 0)])

    def test_memory_operands(self):
        program = assemble("LDR R0, [R1]\nSTR R2, [R3, #4]")
        self.assertEqual(program.instructions[0].args[1], ("mem", 1, 0))
        self.assertEqual(program.instructions[1].args[1], ("mem", 3, 4))

    def test_hex_and_negative_immediates(self):
        program = assemble("MOV R0, #0x10\nMOV R1, #-3")
        self.assertEqual(program.instructions[0].args[1], ("imm", 16))
        self.assertEqual(program.instructions[1].args[1], ("imm", -3))

    def test_data_directive(self):
        program = assemble(".data 10: 1, 2, 3\nHALT")
        self.assertEqual(program.data, {10: 1, 11: 2, 12: 3})
        self.assertEqual(len(program.instructions), 1)

    def test_case_insensitive_opcodes(self):
        program = assemble("mov r0, #1")
        self.assertEqual(program.instructions[0].op, "MOV")


class TestAssemblerErrors(unittest.TestCase):
    def assert_error(self, source, message):
        with self.assertRaises(AssemblyError) as ctx:
            assemble(source)
        self.assertIn(message, str(ctx.exception))

    def test_unknown_instruction(self):
        self.assert_error("JUMP R0", "unknown instruction")

    def test_wrong_operand_count(self):
        self.assert_error("ADD R0, R1", "expects 3 operand(s)")

    def test_invalid_register(self):
        self.assert_error("MOV R9, #1", "R0-R7")

    def test_undefined_label(self):
        self.assert_error("B nowhere", "undefined label")

    def test_duplicate_label(self):
        self.assert_error("a: HALT\na: HALT", "duplicate label")

    def test_wrong_operand_type(self):
        # destination must be a register, not an immediate
        self.assert_error("MOV #1, R0", "does not accept")

    def test_error_reports_line_number(self):
        self.assert_error("HALT\nHALT\nBAD", "line 3")


if __name__ == "__main__":
    unittest.main()
