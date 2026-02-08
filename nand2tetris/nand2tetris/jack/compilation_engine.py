# nand2tetris/jack/compilation_engine.py
from nand2tetris.jack.symbol_table import SymbolTable
from nand2tetris.jack.vm_writer import VMWriter


class CompilationEngine:
    def __init__(self, tokenizer, vm):
        self.tokenizer = tokenizer
        self.vm = vm
        self.symbol_table = SymbolTable()
        self.class_name = ""
        self.label_id = 0

    # ---------- utility ----------

    def eat(self, t=None, v=None):
        if t and self.tokenizer.token_type() != t:
            raise ValueError("Unexpected token type")
        if v and self.tokenizer.token_value() != v:
            raise ValueError("Unexpected token value")
        self.tokenizer.advance()

    def new_label(self, prefix):
        label = f"{prefix}{self.label_id}"
        self.label_id += 1
        return label

    def kind_to_segment(self, kind):
        return {
            "static": "static",
            "field": "this",
            "arg": "argument",
            "var": "local",
        }[kind]

    # ---------- class ----------

    def compile_class(self):
        self.eat("keyword", "class")
        self.class_name = self.tokenizer.token_value()
        self.eat("identifier")
        self.eat("symbol", "{")

        while self.tokenizer.token_value() in ("static", "field"):
            self.compile_class_var_dec()

        while self.tokenizer.token_value() in ("constructor", "function", "method"):
            self.compile_subroutine()

        self.eat("symbol", "}")

    def compile_class_var_dec(self):
        kind = self.tokenizer.token_value()
        self.eat("keyword")
        type_ = self.tokenizer.token_value()
        self.eat(self.tokenizer.token_type())
        name = self.tokenizer.token_value()
        self.eat("identifier")
        self.symbol_table.define(name, type_, kind)

        while self.tokenizer.token_value() == ",":
            self.eat("symbol")
            name = self.tokenizer.token_value()
            self.eat("identifier")
            self.symbol_table.define(name, type_, kind)

        self.eat("symbol", ";")

    # ---------- subroutine ----------

    def compile_subroutine(self):
        self.symbol_table.start_subroutine()

        subroutine_type = self.tokenizer.token_value()
        self.eat("keyword")
        self.eat(self.tokenizer.token_type())  # return type
        name = self.tokenizer.token_value()
        self.eat("identifier")

        if subroutine_type == "method":
            self.symbol_table.define("this", self.class_name, "arg")

        self.eat("symbol", "(")
        self.compile_parameter_list()
        self.eat("symbol", ")")

        self.compile_subroutine_body(subroutine_type, name)

    def compile_parameter_list(self):
        if self.tokenizer.token_value() != ")":
            type_ = self.tokenizer.token_value()
            self.eat(self.tokenizer.token_type())
            name = self.tokenizer.token_value()
            self.eat("identifier")
            self.symbol_table.define(name, type_, "arg")

            while self.tokenizer.token_value() == ",":
                self.eat("symbol")
                type_ = self.tokenizer.token_value()
                self.eat(self.tokenizer.token_type())
                name = self.tokenizer.token_value()
                self.eat("identifier")
                self.symbol_table.define(name, type_, "arg")

    def compile_subroutine_body(self, subroutine_type, name):
        self.eat("symbol", "{")

        while self.tokenizer.token_value() == "var":
            self.compile_var_dec()

        n_locals = self.symbol_table.var_count("var")
        self.vm.write_function(f"{self.class_name}.{name}", n_locals)

        if subroutine_type == "constructor":
            field_count = self.symbol_table.var_count("field")
            self.vm.write_push("constant", field_count)
            self.vm.write_call("Memory.alloc", 1)
            self.vm.write_pop("pointer", 0)

        elif subroutine_type == "method":
            self.vm.write_push("argument", 0)
            self.vm.write_pop("pointer", 0)

        self.compile_statements()
        self.eat("symbol", "}")

    # ---------- statements ----------

    def compile_var_dec(self):
        self.eat("keyword", "var")
        type_ = self.tokenizer.token_value()
        self.eat(self.tokenizer.token_type())
        name = self.tokenizer.token_value()
        self.eat("identifier")
        self.symbol_table.define(name, type_, "var")

        while self.tokenizer.token_value() == ",":
            self.eat("symbol")
            name = self.tokenizer.token_value()
            self.eat("identifier")
            self.symbol_table.define(name, type_, "var")

        self.eat("symbol", ";")

    def compile_statements(self):
        while self.tokenizer.token_value() in ("let", "do", "if", "while", "return"):
            getattr(self, f"compile_{self.tokenizer.token_value()}")()

    # ---------- let / do / return / if / while ----------

    def compile_let(self):
        self.eat("keyword", "let")
        name = self.tokenizer.token_value()
        self.eat("identifier")

        is_array = False
        if self.tokenizer.token_value() == "[":
            is_array = True
            self.eat("symbol", "[")
            self.compile_expression()
            self.eat("symbol", "]")

            kind = self.symbol_table.kind_of(name)
            index = self.symbol_table.index_of(name)
            self.vm.write_push(self.kind_to_segment(kind), index)
            self.vm.write_arithmetic("add")

        self.eat("symbol", "=")
        self.compile_expression()
        self.eat("symbol", ";")

        if is_array:
            self.vm.write_pop("temp", 0)
            self.vm.write_pop("pointer", 1)
            self.vm.write_push("temp", 0)
            self.vm.write_pop("that", 0)
        else:
            kind = self.symbol_table.kind_of(name)
            index = self.symbol_table.index_of(name)
            self.vm.write_pop(self.kind_to_segment(kind), index)

    def compile_do(self):
        self.eat("keyword", "do")
        self.compile_subroutine_call()
        self.vm.write_pop("temp", 0)
        self.eat("symbol", ";")

    def compile_return(self):
        self.eat("keyword", "return")
        if self.tokenizer.token_value() != ";":
            self.compile_expression()
        else:
            self.vm.write_push("constant", 0)
        self.vm.write_return()
        self.eat("symbol", ";")

    def compile_if(self):
        self.eat("keyword", "if")
        self.eat("symbol", "(")
        self.compile_expression()
        self.eat("symbol", ")")

        label_true = self.new_label("IF_TRUE")
        label_false = self.new_label("IF_FALSE")
        label_end = self.new_label("IF_END")

        self.vm.write_if(label_true)
        self.vm.write_goto(label_false)
        self.vm.write_label(label_true)

        self.eat("symbol", "{")
        self.compile_statements()
        self.eat("symbol", "}")

        if self.tokenizer.token_value() == "else":
            self.vm.write_goto(label_end)
            self.vm.write_label(label_false)
            self.eat("keyword", "else")
            self.eat("symbol", "{")
            self.compile_statements()
            self.eat("symbol", "}")
            self.vm.write_label(label_end)
        else:
            self.vm.write_label(label_false)

    def compile_while(self):
        self.eat("keyword", "while")
        label_start = self.new_label("WHILE_EXP")
        label_end = self.new_label("WHILE_END")

        self.vm.write_label(label_start)
        self.eat("symbol", "(")
        self.compile_expression()
        self.eat("symbol", ")")
        self.vm.write_arithmetic("not")
        self.vm.write_if(label_end)

        self.eat("symbol", "{")
        self.compile_statements()
        self.eat("symbol", "}")

        self.vm.write_goto(label_start)
        self.vm.write_label(label_end)

    # ---------- expression / term ----------

    def compile_expression(self):
        self.compile_term()
        while self.tokenizer.token_value() in {"+", "-", "*", "/", "&", "|", "<", ">", "="}:
            op = self.tokenizer.token_value()
            self.eat("symbol")
            self.compile_term()
            self.write_op(op)

    def write_op(self, op):
        mapping = {
            "+": "add",
            "-": "sub",
            "&": "and",
            "|": "or",
            "<": "lt",
            ">": "gt",
            "=": "eq",
        }
        if op in mapping:
            self.vm.write_arithmetic(mapping[op])
        elif op == "*":
            self.vm.write_call("Math.multiply", 2)
        elif op == "/":
            self.vm.write_call("Math.divide", 2)

    def compile_term(self):
        t = self.tokenizer.token_type()
        v = self.tokenizer.token_value()

        if t == "integerConstant":
            self.vm.write_push("constant", int(v))
            self.eat("integerConstant")

        elif t == "stringConstant":
            self.vm.write_push("constant", len(v))
            self.vm.write_call("String.new", 1)
            for c in v:
                self.vm.write_push("constant", ord(c))
                self.vm.write_call("String.appendChar", 2)
            self.eat("stringConstant")

        elif t == "keyword":
            if v == "true":
                self.vm.write_push("constant", 0)
                self.vm.write_arithmetic("not")
            elif v in ("false", "null"):
                self.vm.write_push("constant", 0)
            elif v == "this":
                self.vm.write_push("pointer", 0)
            self.eat("keyword")

        elif t == "symbol" and v in ("-", "~"):
            self.eat("symbol")
            self.compile_term()
            self.vm.write_arithmetic("neg" if v == "-" else "not")

        elif t == "symbol" and v == "(":
            self.eat("symbol", "(")
            self.compile_expression()
            self.eat("symbol", ")")

        elif t == "identifier":
            name = v
            self.eat("identifier")

            if self.tokenizer.token_value() == "[":
                self.eat("symbol", "[")
                self.compile_expression()
                self.eat("symbol", "]")
                kind = self.symbol_table.kind_of(name)
                index = self.symbol_table.index_of(name)
                self.vm.write_push(self.kind_to_segment(kind), index)
                self.vm.write_arithmetic("add")
                self.vm.write_pop("pointer", 1)
                self.vm.write_push("that", 0)

            elif self.tokenizer.token_value() in ("(", "."):
                self.compile_subroutine_call(name)

            else:
                kind = self.symbol_table.kind_of(name)
                index = self.symbol_table.index_of(name)
                self.vm.write_push(self.kind_to_segment(kind), index)

    def compile_subroutine_call(self, name=None):
        if name is None:
            name = self.tokenizer.token_value()
            self.eat("identifier")

        n_args = 0

        if self.tokenizer.token_value() == ".":
            self.eat("symbol", ".")
            sub = self.tokenizer.token_value()
            self.eat("identifier")

            kind = self.symbol_table.kind_of(name)
            if kind:
                segment = self.kind_to_segment(kind)
                index = self.symbol_table.index_of(name)
                self.vm.write_push(segment, index)
                name = f"{self.symbol_table.type_of(name)}.{sub}"
                n_args += 1
            else:
                name = f"{name}.{sub}"
        else:
            self.vm.write_push("pointer", 0)
            name = f"{self.class_name}.{name}"
            n_args += 1

        self.eat("symbol", "(")
        n_args += self.compile_expression_list()
        self.eat("symbol", ")")

        self.vm.write_call(name, n_args)

    def compile_expression_list(self):
        count = 0
        if self.tokenizer.token_value() != ")":
            self.compile_expression()
            count += 1
            while self.tokenizer.token_value() == ",":
                self.eat("symbol")
                self.compile_expression()
                count += 1
        return count
