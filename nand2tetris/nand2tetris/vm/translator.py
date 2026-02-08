# nand2tetris/vm/translator.py
# Project 7: VM Translator（第一阶段）

import sys
from pathlib import Path

# VM 内存段到 Hack 基地址寄存器的映射
SEGMENT_BASE = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}

label_counter = 0
call_counter = 0


def translate_push_segment(segment: str, index: int) -> list[str]:
    """
    翻译：
        push <segment> index
    适用于：local / argument / this / that
    """
    base = SEGMENT_BASE[segment]

    return [
        f"@{index}",
        "D=A",
        f"@{base}",
        "A=M+D",   # A = base + index
        "D=M",     # D = segment[index]

        "@SP",
        "A=M",
        "M=D",     # *SP = D

        "@SP",
        "M=M+1",   # SP++
    ]
def translate_pop_segment(segment: str, index: int) -> list[str]:
    """
    翻译：
        pop <segment> index
    """
    base = SEGMENT_BASE[segment]

    return [
        f"@{index}",
        "D=A",
        f"@{base}",
        "D=M+D",   # D = base + index
        "@R13",
        "M=D",     # R13 = 目标地址

        "@SP",
        "M=M-1",   # SP--
        "A=M",
        "D=M",     # D = 栈顶值

        "@R13",
        "A=M",
        "M=D",     # segment[index] = 栈顶值
    ]

def translate_push_constant(value: int) -> list[str]:
    """
    翻译 VM 指令：
        push constant value

    返回对应的 Hack 汇编指令列表
    """
    return [
        f"@{value}",   # A = value
        "D=A",         # D = value
        "@SP",         # A = SP
        "A=M",         # A = *SP（栈顶）
        "M=D",         # *SP = value
        "@SP",
        "M=M+1",       # SP++
    ]

def translate_add() -> list[str]:
    """
    翻译：
        add
    """
    return [
        "@SP",
        "M=M-1",   # SP--
        "A=M",
        "D=M",     # D = x

        "@SP",
        "M=M-1",
        "A=M",
        "M=M+D",   # y = y + x

        "@SP",
        "M=M+1",   # SP++
    ]
def translate_sub() -> list[str]:
    """
    翻译：
        sub
    """
    return [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",     # D = x

        "@SP",
        "M=M-1",
        "A=M",
        "M=M-D",   # y = y - x

        "@SP",
        "M=M+1",
    ]
def translate_neg() -> list[str]:
    """
    翻译：
        neg
    """
    return [
        "@SP",
        "M=M-1",
        "A=M",
        "M=-M",    # x = -x

        "@SP",
        "M=M+1",
    ]
def translate_and() -> list[str]:
    """
    翻译：
        and
    """
    return [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",     # D = x

        "@SP",
        "M=M-1",
        "A=M",
        "M=M&D",   # y = y & x

        "@SP",
        "M=M+1",
    ]
def translate_or() -> list[str]:
    """
    翻译：
        or
    """
    return [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",     # D = x

        "@SP",
        "M=M-1",
        "A=M",
        "M=M|D",   # y = y | x

        "@SP",
        "M=M+1",
    ]
def translate_not() -> list[str]:
    """
    翻译：
        not
    """
    return [
        "@SP",
        "M=M-1",
        "A=M",
        "M=!M",    # x = ~x

        "@SP",
        "M=M+1",
    ]

def translate_compare(jump: str) -> list[str]:
    """
    通用比较指令翻译
    jump: JEQ / JGT / JLT
    """
    global label_counter
    idx = label_counter
    label_counter += 1

    true_label = f"TRUE_{idx}"
    end_label = f"END_{idx}"

    return [
        # 弹出 x
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",

        # 弹出 y，计算 y - x
        "@SP",
        "M=M-1",
        "A=M",
        "D=M-D",

        # 默认写入 false (0)
        "@SP",
        "A=M",
        "M=0",

        # 如果条件满足，跳转写 true
        f"@{true_label}",
        f"D;{jump}",

        # 跳到结束
        f"@{end_label}",
        "0;JMP",

        # true 分支
        f"({true_label})",
        "@SP",
        "A=M",
        "M=-1",

        # 结束
        f"({end_label})",
        "@SP",
        "M=M+1",
    ]
def translate_eq() -> list[str]:
    return translate_compare("JEQ")
def translate_gt() -> list[str]:
    return translate_compare("JGT")
def translate_lt() -> list[str]:
    return translate_compare("JLT")

def translate_push_temp(index: int) -> list[str]:
    """
    temp 段：RAM[5 + index]
    """
    addr = 5 + index
    return [
        f"@{addr}",
        "D=M",

        "@SP",
        "A=M",
        "M=D",

        "@SP",
        "M=M+1",
    ]
def translate_pop_temp(index: int) -> list[str]:
    """
    temp 段：RAM[5 + index]
    """
    addr = 5 + index
    return [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",

        f"@{addr}",
        "M=D",
    ]
def translate_push_pointer(index: int) -> list[str]:
    base = "THIS" if index == 0 else "THAT"
    return [
        f"@{base}",
        "D=M",

        "@SP",
        "A=M",
        "M=D",

        "@SP",
        "M=M+1",
    ]
def translate_pop_pointer(index: int) -> list[str]:
    base = "THIS" if index == 0 else "THAT"
    return [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",

        f"@{base}",
        "M=D",
    ]
def translate_push_static(file_stem: str, index: int) -> list[str]:
    symbol = f"{file_stem}.{index}"
    return [
        f"@{symbol}",
        "D=M",

        "@SP",
        "A=M",
        "M=D",

        "@SP",
        "M=M+1",
    ]
def translate_pop_static(file_stem: str, index: int) -> list[str]:
    symbol = f"{file_stem}.{index}"
    return [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",

        f"@{symbol}",
        "M=D",
    ]


def translate_function(name: str, n_vars: int) -> list[str]:
    """
    翻译：
        function f nVars
    """
    asm = [
        f"({name})"  # 函数入口标签
    ]

    # 初始化 n_vars 个局部变量为 0
    for _ in range(n_vars):
        asm.extend([
            "@0",
            "D=A",

            "@SP",
            "A=M",
            "M=D",

            "@SP",
            "M=M+1",
        ])

    return asm
def translate_return() -> list[str]:
    """
    翻译：
        return
    """
    return [
        # FRAME = LCL
        "@LCL",
        "D=M",
        "@R13",
        "M=D",

        # RET = *(FRAME - 5)
        "@5",
        "A=D-A",
        "D=M",
        "@R14",
        "M=D",

        # *ARG = pop()
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",

        "@ARG",
        "A=M",
        "M=D",

        # SP = ARG + 1
        "@ARG",
        "D=M+1",
        "@SP",
        "M=D",

        # THAT = *(FRAME - 1)
        "@R13",
        "AM=M-1",
        "D=M",
        "@THAT",
        "M=D",

        # THIS = *(FRAME - 2)
        "@R13",
        "AM=M-1",
        "D=M",
        "@THIS",
        "M=D",

        # ARG = *(FRAME - 3)
        "@R13",
        "AM=M-1",
        "D=M",
        "@ARG",
        "M=D",

        # LCL = *(FRAME - 4)
        "@R13",
        "AM=M-1",
        "D=M",
        "@LCL",
        "M=D",

        # goto RET
        "@R14",
        "A=M",
        "0;JMP",
    ]
def translate_call(func_name: str, n_args: int) -> list[str]:
    """
    翻译：
        call f nArgs
    """
    global call_counter
    ret_label = f"RETURN_LABEL_{call_counter}"
    call_counter += 1

    asm = [
        # push return-address
        f"@{ret_label}",
        "D=A",
        "@SP",
        "A=M",
        "M=D",
        "@SP",
        "M=M+1",
    ]

    # push LCL, ARG, THIS, THAT
    for seg in ["LCL", "ARG", "THIS", "THAT"]:
        asm.extend([
            f"@{seg}",
            "D=M",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        ])

    # ARG = SP - nArgs - 5
    asm.extend([
        "@SP",
        "D=M",
        f"@{n_args}",
        "D=D-A",
        "@5",
        "D=D-A",
        "@ARG",
        "M=D",
    ])

    # LCL = SP
    asm.extend([
        "@SP",
        "D=M",
        "@LCL",
        "M=D",
    ])

    # goto f
    asm.extend([
        f"@{func_name}",
        "0;JMP",
        f"({ret_label})",
    ])

    return asm

def translate_label(label: str) -> list[str]:
    """
    翻译：
        label LABEL_NAME
    """
    return [f"({label})"]


def translate_goto(label: str) -> list[str]:
    """
    翻译：
        goto LABEL_NAME
    """
    return [
        f"@{label}",
        "0;JMP",
    ]


def translate_if_goto(label: str) -> list[str]:
    """
    翻译：
        if-goto LABEL_NAME
    从栈顶弹出值，如果非零则跳转到标签
    """
    return [
        "@SP",
        "M=M-1",   # SP--
        "A=M",
        "D=M",     # D = 栈顶值
        f"@{label}",
        "D;JNE",   # 如果 D != 0 则跳转
    ]


def bootstrap_code() -> list[str]:
    return [
        # SP = 256
        "@256",
        "D=A",
        "@SP",
        "M=D",

        # 调用 Sys.init
        "@Sys.init",
        "0;JMP"
    ]




def translate_line(line: str, file_stem: str) -> list[str]:
    parts = line.split()
    command = parts[0]

    # 1. 算术 / 逻辑指令（1个单词）
    if command in ("add", "sub", "neg", "and", "or", "not", "eq", "gt", "lt"):
        if command == "add":
            return translate_add()
        if command == "sub":
            return translate_sub()
        if command == "neg":
            return translate_neg()
        if command == "and":
            return translate_and()
        if command == "or":
            return translate_or()
        if command == "not":
            return translate_not()
        if command == "eq":
            return translate_eq()
        if command == "gt":
            return translate_gt()
        if command == "lt":
            return translate_lt()

    # 2. return 指令（1个单词）
    if command == "return":
        return translate_return()

    # 3. label 指令（2个单词）
    if command == "label":
        if len(parts) < 2:
            raise ValueError(f"Unsupported VM instruction: {line}")
        label_name = parts[1]
        return translate_label(label_name)

    # 4. goto 指令（2个单词）
    if command == "goto":
        if len(parts) < 2:
            raise ValueError(f"Unsupported VM instruction: {line}")
        label_name = parts[1]
        return translate_goto(label_name)

    # 5. if-goto 指令（2个单词）
    if command == "if-goto":
        if len(parts) < 2:
            raise ValueError(f"Unsupported VM instruction: {line}")
        label_name = parts[1]
        return translate_if_goto(label_name)

    # 6. 内存访问和函数调用指令（3个单词）
    if len(parts) < 3:
        raise ValueError(f"Unsupported VM instruction: {line}")

    segment = parts[1]
    index_or_count = int(parts[2])

    # push/pop 指令
    if command == "push":
        if segment == "constant":
            return translate_push_constant(index_or_count)
        if segment in SEGMENT_BASE:
            return translate_push_segment(segment, index_or_count)
        if segment == "temp":
            return translate_push_temp(index_or_count)
        if segment == "pointer":
            return translate_push_pointer(index_or_count)
        if segment == "static":
            return translate_push_static(file_stem, index_or_count)

    if command == "pop":
        if segment in SEGMENT_BASE:
            return translate_pop_segment(segment, index_or_count)
        if segment == "temp":
            return translate_pop_temp(index_or_count)
        if segment == "pointer":
            return translate_pop_pointer(index_or_count)
        if segment == "static":
            return translate_pop_static(file_stem, index_or_count)

    # function/call 指令
    if command == "function":
        func_name = parts[1]
        n_vars = int(parts[2])
        return translate_function(func_name, n_vars)

    if command == "call":
        func_name = parts[1]
        n_args = int(parts[2])
        return translate_call(func_name, n_args)

    raise ValueError(f"Unsupported VM instruction: {line}")





def main(argv=None):
    """
    VM Translator CLI 入口
    支持两种使用方式：
    1. nand2tetris vm Prog.vm      - 翻译单个VM文件，输出到stdout
    2. nand2tetris vm DirName      - 翻译目录下所有VM文件，输出到DirName/DirName.asm
    """
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print("Usage: nand2tetris vm <file.vm | directory>", file=sys.stderr)
        sys.exit(1)

    path = Path(argv[0])
    
    if path.is_file():
        # 单个文件：直接翻译并输出到stdout
        _translate_file(path)
    elif path.is_dir():
        # 目录：翻译所有VM文件，输出到 <dir>/<dir>.asm
        _translate_directory(path)
    else:
        print(f"Error: '{argv[0]}' is neither a file nor a directory", file=sys.stderr)
        sys.exit(1)


def _translate_file(vm_file: Path):
    """
    翻译单个VM文件，输出到stdout
    """
    with vm_file.open() as f:
        lines = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("//")
        ]

    file_stem = vm_file.stem
    for line in lines:
        asm_lines = translate_line(line, file_stem)
        for asm in asm_lines:
            print(asm)


def _translate_directory(directory: Path):
    """
    翻译目录下所有VM文件，输出到 <directory>/<directory.name>.asm
    """
    vm_files = sorted(directory.glob("*.vm"))
    
    if not vm_files:
        print(f"Warning: No .vm files found in {directory}", file=sys.stderr)
        return
    
    asm_output = []
    
    for vm_file in vm_files:
        with vm_file.open() as f:
            lines = [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("//")
            ]
        
        file_stem = vm_file.stem
        for line in lines:
            asm_lines = translate_line(line, file_stem)
            asm_output.extend(asm_lines)
    
    # 生成输出文件：<directory>/<directory.name>.asm
    output_file = directory / f"{directory.name}.asm"
    with output_file.open("w") as f:
        f.write("\n".join(asm_output) + "\n")
    
    print(f"Generated: {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()

