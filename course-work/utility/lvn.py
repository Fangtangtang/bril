from .cfg import BasicBlock
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

commutative = {"ne", "eq", "feq", "and", "or", "add", "mul", "fadd", "fmul"}


class Const:
    def __init__(self, value):
        self.val = value
        self.dtype = type(value).__name__

    def __eq__(self, other):
        if not isinstance(other, Const):
            return NotImplemented
        return self.val == other.val and self.dtype == other.dtype

    def __repr__(self):
        return f"Const(val={self.val}, dtype={self.dtype})"
    
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

    def add_entry(self, value, name) -> int:
        table_entry = LVNTableEntry(value, name)
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

def run_lvn(bb:BasicBlock, live_in: dict = None):
    rename_map: dict[str, str] = {}
    var2num: dict[str, int] = {}
    lvn_table = LVNTable()
    for instr_node in bb.instr_nodes:
        instr= instr_node.val
        args = []
        if "args" in instr.instr:
            for i, arg in enumerate(instr.instr["args"]):
                if arg in rename_map:
                    arg = rename_map[arg]
                if arg not in var2num:
                    if live_in is not None and arg in live_in:
                        idx = lvn_table.add_entry(live_in[arg], arg)
                    else:
                        idx = lvn_table.add_entry(arg, arg)
                    var2num[arg] = idx
                    rename_map[arg] = arg
                    args.append(idx)
                else:
                    idx = var2num[arg]
                    instr.instr["args"][i] = lvn_table.table[idx].name
                    args.append(idx)
        if "op" in instr.instr and "dest" in instr.instr:
            dest = instr.instr["dest"]
            op = instr.instr["op"]
            if op == "const":
                value = instr.instr["value"]
                if instr.instr["type"] == "float":
                    value = float(value)
                elif instr.instr["type"] == "bool":
                    value = bool(value)
                args.append(value)
            elif op == "call":
                op += f"@{instr.instr["funcs"]}"
            idx, new_name = lvn_table.find_value(op, args, dest)
            if new_name is not None:
                rename_map[dest] = new_name
                var2num[new_name] = idx
                instr.instr["dest"] = new_name
            else:
                rename_map[dest] = dest
                var2num[dest] = idx
            if isinstance(lvn_table.table[idx].value, Const):
                dest = instr.instr["dest"]
                instr.instr.clear()
                instr.instr["dest"] = dest
                instr.instr["op"] = "const"
                instr.instr["type"] = lvn_table.table[idx].value.dtype
                instr.instr["value"] = lvn_table.table[idx].value.val
    rename ={}
    for name_, new_name_ in rename_map.items():
        if name_ != new_name_:
            rename[new_name_] = name_
    for instr_node in bb.instr_nodes:
        instr = instr_node.val
        if "args" in instr.instr:
            for i, arg in enumerate(instr.instr["args"]):
                if arg in rename:
                    instr.instr["args"][i]= rename[arg]
        if "dest" in instr.instr and  instr.instr["dest"] in rename:
            instr.instr["dest"] = rename[ instr.instr["dest"]]
