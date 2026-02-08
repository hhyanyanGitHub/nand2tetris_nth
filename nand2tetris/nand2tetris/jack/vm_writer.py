# nand2tetris/jack/vm_writer.py

class VMWriter:
    def __init__(self, out):
        self.out = out

    def write_push(self, segment, index):
        self.out.write(f"push {segment} {index}\n")

    def write_pop(self, segment, index):
        self.out.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command):
        self.out.write(f"{command}\n")

    def write_label(self, label):
        self.out.write(f"label {label}\n")

    def write_goto(self, label):
        self.out.write(f"goto {label}\n")

    def write_if(self, label):
        self.out.write(f"if-goto {label}\n")

    def write_call(self, name, n_args):
        self.out.write(f"call {name} {n_args}\n")

    def write_function(self, name, n_locals):
        self.out.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.out.write("return\n")
