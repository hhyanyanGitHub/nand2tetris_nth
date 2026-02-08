# nand2tetris/jack/tokenizer.py
import re

KEYWORDS = {
    "class", "constructor", "function", "method", "field", "static",
    "var", "int", "char", "boolean", "void",
    "true", "false", "null", "this",
    "let", "do", "if", "else", "while", "return"
}

SYMBOLS = "{}()[].,;+-*/&|<>=~"


class JackTokenizer:
    def __init__(self, path):
        with open(path) as f:
            source = f.read()

        source = re.sub(r"//.*", "", source)
        source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)

        token_pattern = r'"[^"\n]*"|[A-Za-z_]\w*|\d+|[' + re.escape(SYMBOLS) + r']'
        self.tokens = re.findall(token_pattern, source)

        self.index = 0
        self.current = None
        self.advance()

    def advance(self):
        if self.index < len(self.tokens):
            self.current = self.tokens[self.index]
            self.index += 1
        else:
            self.current = None

    def token_type(self):
        if self.current is None:
            return None
        if self.current in KEYWORDS:
            return "keyword"
        if self.current in SYMBOLS:
            return "symbol"
        if self.current.isdigit():
            return "integerConstant"
        if self.current.startswith('"'):
            return "stringConstant"
        return "identifier"

    def token_value(self):
        if self.current is None:
            return None
        if self.token_type() == "stringConstant":
            return self.current[1:-1]
        return self.current
