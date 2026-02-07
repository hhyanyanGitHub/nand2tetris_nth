import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: nand2tetris <command> [args...]")
        print("Commands: asm, vm, jack")
        sys.exit(1)

    command = sys.argv[1]

    if command == "asm":
        from nand2tetris.asm.assembler import main as asm_main
        asm_main(sys.argv[2:])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

