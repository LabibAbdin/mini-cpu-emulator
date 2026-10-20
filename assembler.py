"""
Two-pass assembler: turns assembly source text into a Program the CPU can run.

Pass 1 finds every label and remembers which instruction it points to.
Pass 2 parses each instruction and replaces label names with addresses.
Two passes are needed because a branch can jump *forward* to a label
that hasn't been seen yet (e.g. `BEQ done` before `done:` is defined).
"""

import re
from dataclasses import dataclass, field


class AssemblyError(Exception):
    """Raised when the source code has a syntax or semantic error."""


@dataclass
class Instruction:
    op: str        # e.g. "ADD"
    args: list     # parsed operands, e.g. [("reg", 0), ("reg", 1), ("imm", 5)]
    line: int      # source line number, used in error messages
    text: str      # original source text, used in trace output


@dataclass
class Program:
    instructions: list
    labels: dict = field(default_factory=dict)  # label name -> instruction index
    data: dict = field(default_factory=dict)    # memory address -> initial value


NUM_REGISTERS = 8

# For each instruction: the operand kinds allowed in each position.
# "reg" = register (R0-R7), "imm" = immediate number (#5),
# "mem" = memory address in a register ([R1] or [R1, #4]), "label" = branch target.
SYNTAX = {
    "MOV":  [("reg",), ("reg", "imm")],
    "ADD":  [("reg",), ("reg",), ("reg", "imm")],
    "SUB":  [("reg",), ("reg",), ("reg", "imm")],
    "MUL":  [("reg",), ("reg",), ("reg", "imm")],
    "CMP":  [("reg",), ("reg", "imm")],
    "LDR":  [("reg",), ("mem",)],
    "STR":  [("reg",), ("mem",)],
    "B":    [("label",)],
    "BEQ":  [("label",)],
    "BNE":  [("label",)],
    "BLT":  [("label",)],
    "BGT":  [("label",)],
    "HALT": [],
}

LABEL_RE = re.compile(r"^([A-Za-z_]\w*):")
REGISTER_RE = re.compile(r"^[Rr]\d+$")
# Splits "R1, [R2, #4]" into ["R1", "[R2, #4]"] without breaking up the brackets.
OPERAND_RE = re.compile(r"\[[^\]]*\]|[^,\s]+")


def assemble(source):
    """Assemble source text into a Program. Raises AssemblyError on bad input."""
    labels = {}
    data = {}
    pending = []  # (line_number, instruction_text) collected in pass 1

    # ---- Pass 1: find labels, data directives and instruction lines ----
    for line_no, raw in enumerate(source.splitlines(), start=1):
        text = raw.split(";", 1)[0].strip()  # remove comments
        if not text:
            continue

        match = LABEL_RE.match(text)
        if match:
            name = match.group(1)
            if name in labels:
                raise AssemblyError(f"line {line_no}: duplicate label '{name}'")
            labels[name] = len(pending)  # label points at the next instruction
            text = text[match.end():].strip()
            if not text:
                continue

        if text.lower().startswith(".data"):
            _parse_data(text, line_no, data)
        else:
            pending.append((line_no, text))

    # ---- Pass 2: parse instructions and resolve labels ----
    instructions = [_parse_instruction(text, line_no, labels) for line_no, text in pending]
    return Program(instructions, labels, data)


def _parse_data(text, line_no, data):
    """Parse a directive like `.data 100: 4, 8, 15` (values stored from address 100)."""
    try:
        address_part, values_part = text[len(".data"):].split(":", 1)
        address = int(address_part.strip(), 0)
        values = [int(v.strip(), 0) for v in values_part.split(",") if v.strip()]
    except ValueError:
        raise AssemblyError(f"line {line_no}: expected '.data ADDRESS: VALUE, VALUE, ...'")
    for offset, value in enumerate(values):
        data[address + offset] = value


def _parse_instruction(text, line_no, labels):
    parts = text.split(None, 1)
    op = parts[0].upper()
    operand_text = parts[1] if len(parts) > 1 else ""

    if op not in SYNTAX:
        raise AssemblyError(f"line {line_no}: unknown instruction '{parts[0]}'")

    raw_operands = OPERAND_RE.findall(operand_text)
    expected = SYNTAX[op]
    if len(raw_operands) != len(expected):
        raise AssemblyError(
            f"line {line_no}: {op} expects {len(expected)} operand(s), got {len(raw_operands)}"
        )

    args = []
    for raw, allowed in zip(raw_operands, expected):
        operand = _parse_operand(raw, line_no, labels)
        if operand[0] not in allowed:
            raise AssemblyError(
                f"line {line_no}: {op} does not accept '{raw}' here (expected {' or '.join(allowed)})"
            )
        args.append(operand)

    return Instruction(op, args, line_no, text)


def _parse_operand(raw, line_no, labels):
    """Turn one operand string into a tuple like ("reg", 3) or ("imm", 42)."""
    if REGISTER_RE.match(raw):
        return ("reg", _parse_register(raw, line_no))

    if raw.startswith("#"):
        try:
            return ("imm", int(raw[1:], 0))  # base 0 allows #10, #0x1F, #-3
        except ValueError:
            raise AssemblyError(f"line {line_no}: bad immediate value '{raw}'")

    if raw.startswith("["):
        # [R1] or [R1, #offset]
        inner = [p.strip() for p in raw.strip("[]").split(",")]
        base = _parse_register(inner[0], line_no)
        offset = 0
        if len(inner) == 2 and inner[1].startswith("#"):
            try:
                offset = int(inner[1][1:], 0)
            except ValueError:
                raise AssemblyError(f"line {line_no}: bad offset in '{raw}'")
        elif len(inner) != 1:
            raise AssemblyError(f"line {line_no}: bad memory operand '{raw}'")
        return ("mem", base, offset)

    if raw in labels:
        return ("label", labels[raw])
    raise AssemblyError(f"line {line_no}: undefined label or bad operand '{raw}'")


def _parse_register(raw, line_no):
    try:
        number = int(raw[1:])
    except ValueError:
        raise AssemblyError(f"line {line_no}: bad register '{raw}'")
    if not (raw[0] in "Rr" and 0 <= number < NUM_REGISTERS):
        raise AssemblyError(f"line {line_no}: register must be R0-R{NUM_REGISTERS - 1}, got '{raw}'")
    return number
