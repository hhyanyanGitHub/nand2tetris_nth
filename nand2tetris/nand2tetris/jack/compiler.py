# nand2tetris/jack/compiler.py
import os
from nand2tetris.jack.tokenizer import JackTokenizer
from nand2tetris.jack.compilation_engine import CompilationEngine
from nand2tetris.jack.vm_writer import VMWriter


def compile_single_file(path):
    out_path = path.replace(".jack", ".vm")
    with open(out_path, "w") as out:
        tokenizer = JackTokenizer(path)
        vm = VMWriter(out)
        engine = CompilationEngine(tokenizer, vm)
        engine.compile_class()


def compile_path(path):
    if os.path.isdir(path):
        for f in os.listdir(path):
            if f.endswith(".jack"):
                compile_single_file(os.path.join(path, f))
    else:
        compile_single_file(path)


def main(argv):
    if len(argv) != 1:
        raise ValueError("Usage: jack <file|directory>")
    compile_path(argv[0])
