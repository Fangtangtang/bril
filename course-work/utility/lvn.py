
op_map = {
    "ne":"!=",
    "eq": "==",
    "le": "<=",
    "lt": "<",
    "gt": ">",
    "ge": ">=",
    "and": "and",
    "or": "or",
    "not": "not",
    "add": "+",
    "sub": "-",
    "mul": "*",
    "div": "//"
}

commutative = {
    "ne", "eq", "and","or", "add", "mul"
}
class Const:
    def __init__(self, value, dtype):
        self.val = value
        self.dtype=dtype

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
        self.table:list[LVNTableEntry] = []

    def add_entry(self, name) -> int:
        table_entry = LVNTableEntry(name, name)
        self.table.append(table_entry)
        return len(self.table)-1

    def find_value(self, op, args, name) -> tuple[int, str]:
        if op == "const":
            val = Const(args[0], str(type(args[0])))
        elif op in commutative:
            operand1, operand2 = args[0], args[1]
            if operand1 > operand2:
                operand1, operand2 = operand2, operand1
            val = (op, [operand1, operand2])
        else: 
            val = (op, args)
        for i, entry in enumerate(self.table):
            if entry.value == val:
                return (i, None)
        new_name = f"{name}_{len(self.table)}"
        table_entry = LVNTableEntry(val, new_name)
        self.table.append(table_entry)
        return (len(self.table)-1, new_name)



        
