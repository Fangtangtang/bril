# TODO: use eval to perform some constant folding
op_map = {
    "ne": "!=",
    "eq": "==",
    "le": "<=",
    "lt": "<",
    "gt": ">",
    "ge": ">=",
    "feq": "==",
    "fle": "<=",
    "flt": "<",
    "fgt": ">",
    "fge": ">=",
    "and": "and",
    "or": "or",
    "not": "not",
    "add": "+",
    "sub": "-",
    "mul": "*",
    "div": "//",
    "fadd": "+",
    "fsub": "-",
    "fmul": "*",
    "fdiv": "/",
}

commutative = {"ne", "eq", "and", "or", "add", "mul"}


class Const:
    def __init__(self, value):
        self.val = value
        self.dtype = type(value).__name__


class LVNTableEntry:
    def __init__(self, value, name):
        self.value = value
        self.name = name

    def __str__(self):
        return f"{self.name}:\t{self.value}"

    def __repr__(self):
        return self.__str__()


class LVNTable:
    def __init__(self):
        self.table: list[LVNTableEntry] = []

    def add_entry(self, name) -> int:
        table_entry = LVNTableEntry(name, name)
        self.table.append(table_entry)
        return len(self.table) - 1

    def find_value(self, op, args, name) -> tuple[int, str]:
        if op == "const":
            val = Const(args[0])
        elif op in commutative:
            operand1, operand2 = args[0], args[1]
            if operand1 > operand2:
                operand1, operand2 = operand2, operand1
            val = (op, [operand1, operand2])
        else:
            val = (op, args)
        if op in op_map:
            const_arg = []
            for arg in args:
                if isinstance(self.table[arg].value, Const):
                    const_arg.append(self.table[arg].value.val)
                else:
                    break
            if len(const_arg) == len(args):
                try:
                    if len(const_arg) == 1:
                        result_val = eval(f"{op_map[op]} {const_arg[0]}")
                    elif len(const_arg) == 2:
                        result_val = eval(f"{const_arg[0]} {op_map[op]} {const_arg[1]}")
                    val = Const(result_val)
                except:
                    # e.g. div 0 should raise error at run time
                    pass
        for i, entry in enumerate(self.table):
            if entry.value == val:
                return (i, None)
        new_name = f"{name}_{len(self.table)}"
        table_entry = LVNTableEntry(val, new_name)
        self.table.append(table_entry)
        return (len(self.table) - 1, new_name)
