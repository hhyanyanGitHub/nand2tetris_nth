# nand2tetris/cli.py
# 统一命令行入口：nand2tetris <command> [args...]

import sys


def main():
    # sys.argv:
    #   argv[0] -> 模块名
    #   argv[1] -> 子命令（asm / vm / jack）
    if len(sys.argv) < 2:
        print("Usage: nand2tetris <command> [args...]")
        print("Commands:")
        print("  asm   Hack 汇编器（Project 6）")
        print("  vm    VM 翻译器（Project 7–8）")
        print("  jack  Jack 编译器（Project 10–11）")
        sys.exit(1)

    command = sys.argv[1]

    # 根据子命令分发到不同模块
    # 注意：CLI 只做“路由”，不做任何业务逻辑
    if command == "asm":
        # 延迟 import：避免无关模块被加载
        from nand2tetris.asm.assembler import main as asm_main

        # 把剩余参数传给 assembler
        asm_main(sys.argv[2:])

    elif command == "vm":
        from nand2tetris.vm.translator import main as vm_main
        vm_main(sys.argv[2:])

    elif command == "jack":
        from nand2tetris.jack.compiler import main as jack_main
        jack_main(sys.argv[2:])

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

