"""
Hack Assembler for nand2tetris (Software Project 6)
Guided by MIT 'The Missing Semester of Your CS Education' principles:
- Command-line first
- Small composable functions
- Deterministic builds
- Debuggable and testable

Usage:
  python assembler.py Prog.asm > Prog.hack
"""

import sys
import re
from typing import Dict, List

# -----------------------------
# Symbol Table
# -----------------------------

PREDEFINED_SYMBOLS: Dict[str, int] = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    **{f"R{i}": i for i in range(16)},
    "SCREEN": 16384,
    "KBD": 24576,
}

# -----------------------------
# C-instruction tables
# -----------------------------

DEST = {
    None: "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111",
}

JUMP = {
    None: "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}

COMP = {
    "0":   "0101010",
    "1":   "0111111",
    "-1":  "0111010",
    "D":   "0001100",
    "A":   "0110000",
    "!D":  "0001101",
    "!A":  "0110001",
    "-D":  "0001111",
    "-A":  "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",
    "M":   "1110000",
    "!M":  "1110001",
    "-M":  "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101",
}

# -----------------------------
# Parsing utilities
# -----------------------------

def clean_line(line: str) -> str | None:
    line = re.sub(r"//.*", "", line).strip()
    return line if line else None


def parse_c_instruction(instr: str):
    dest, comp, jump = None, None, None
    if '=' in instr:
        dest, instr = instr.split('=')
    if ';' in instr:
        comp, jump = instr.split(';')
    else:
        comp = instr
    return dest, comp, jump

# -----------------------------
# Assembler passes
# -----------------------------

def first_pass(lines: List[str]) -> Dict[str, int]:
    symbols = dict(PREDEFINED_SYMBOLS)
    rom_addr = 0
    for line in lines:
        if line.startswith('(') and line.endswith(')'):
            label = line[1:-1]
            symbols[label] = rom_addr
        else:
            rom_addr += 1
    return symbols


def second_pass(lines: List[str], symbols: Dict[str, int]) -> List[str]:
    result = []
    next_var_addr = 16

    for line in lines:
        if line.startswith('('):
            continue

        # A-instruction
        if line.startswith('@'):
            symbol = line[1:]
            if symbol.isdigit():
                addr = int(symbol)
            else:
                if symbol not in symbols:
                    symbols[symbol] = next_var_addr
                    next_var_addr += 1
                addr = symbols[symbol]
            result.append(f"0{addr:015b}")
            continue

        # C-instruction
        dest, comp, jump = parse_c_instruction(line)
        try:
            code = "111" + COMP[comp] + DEST[dest] + JUMP[jump]
        except KeyError:
            raise ValueError(f"Invalid C-instruction: {line}")
        result.append(code)

    return result

# -----------------------------
# CLI entry
# -----------------------------

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print("Usage: asm Prog.asm", file=sys.stderr)
        sys.exit(1)
    filename = argv[0]

    with open(filename) as f:
        raw_lines = f.readlines()

    lines = list(filter(None, (clean_line(l) for l in raw_lines)))
    symbols = first_pass(lines)
    machine_code = second_pass(lines, symbols)

    for code in machine_code:
        print(code)


if __name__ == "__main__":
    main()

