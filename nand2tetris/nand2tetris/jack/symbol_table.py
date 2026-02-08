# nand2tetris/jack/symbol_table.py

class SymbolTable:
    def __init__(self):
        self.class_scope = {}
        self.subroutine_scope = {}
        self.counts = {"static": 0, "field": 0, "arg": 0, "var": 0}

    def start_subroutine(self):
        self.subroutine_scope = {}
        self.counts["arg"] = 0
        self.counts["var"] = 0

    def define(self, name, type_, kind):
        index = self.counts[kind]
        self.counts[kind] += 1
        entry = {"type": type_, "kind": kind, "index": index}

        if kind in ("static", "field"):
            self.class_scope[name] = entry
        else:
            self.subroutine_scope[name] = entry

    def kind_of(self, name):
        return (
            self.subroutine_scope.get(name, self.class_scope.get(name, {}))
            .get("kind")
        )

    def type_of(self, name):
        return (
            self.subroutine_scope.get(name, self.class_scope.get(name, {}))
            .get("type")
        )

    def index_of(self, name):
        return (
            self.subroutine_scope.get(name, self.class_scope.get(name, {}))
            .get("index")
        )

    def var_count(self, kind):
        return self.counts[kind]
