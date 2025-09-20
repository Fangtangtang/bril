import sys
import json
from utility.cfg import construct_cfg, BasicBlock, Instruction
from utility.lvn import LVNTable, Const
from utility.transform import clean

# [NOTE]: for benchmarks/core, benchmarks/float, benchmarks/long

def dce_v1(program):
    for func in program["functions"]:
        updated = True
        while updated:
            updated = False
            used = set()
            for inst in func["instrs"]:
                if inst is not None and "args" in inst:
                    for arg in inst["args"]:
                        used.add(arg)
            for idx, inst in enumerate(func["instrs"]):
                if inst is not None and "dest" in inst and not inst["dest"] in used:
                    func["instrs"][idx] = None
                    updated = True
        clean(func)
    return program


def dce_v2(program):
    update = False
    for func in program["functions"]:
        bbs: dict[str, BasicBlock] = construct_cfg(func)
        for bb in bbs.values():
            used_with_def = {}
            for i in range(len(bb.instrs)):
                idx = len(bb.instrs) - 1 - i
                inst: Instruction = bb.instrs[idx]
                if inst is not None:
                    if "dest" in inst.instr:
                        if (
                            inst.instr["dest"] in used_with_def
                            and used_with_def[inst.instr["dest"]]
                        ):
                            func["instrs"][inst.idx] = None
                            continue
                        used_with_def[inst.instr["dest"]] = True
                    if "args" in inst.instr:
                        for arg in inst.instr["args"]:
                            used_with_def[arg] = False
        updated = True
        while updated:
            updated = False
            used = set()
            for inst in func["instrs"]:
                if inst is not None and "args" in inst:
                    for arg in inst["args"]:
                        used.add(arg)
            for idx, inst in enumerate(func["instrs"]):
                if inst is not None and "dest" in inst and not inst["dest"] in used:
                    func["instrs"][idx] = None
                    updated = True
        if clean(func):
            updated = True
    return updated


def lvn(func):
    bbs: dict[str, BasicBlock] = construct_cfg(func)
    
    for bb in bbs.values():
        rename_map: dict[str, str] = {}
        var2num: dict[str, int] = {}
        lvn_table = LVNTable()
        for instr in bb.instrs:
            args = []
            if "args" in instr.instr:
                for i, arg in enumerate(instr.instr["args"]):
                    if arg in rename_map:
                        arg = rename_map[arg]
                    if arg not in var2num:
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
        for instr in bb.instrs:
            if "args" in instr.instr:
                for i, arg in enumerate(instr.instr["args"]):
                    if arg in rename:
                        instr.instr["args"][i]= rename[arg]
            if "dest" in instr.instr and  instr.instr["dest"] in rename:
                instr.instr["dest"] = rename[ instr.instr["dest"]]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads("".join(sys.stdin.readlines()))
    for func in program["functions"]:
        lvn(func)
    # print(json.dumps((program)))
    dce_v2(program)
    print(json.dumps(program))
