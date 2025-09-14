import sys
import json
from utility.cfg import construct_cfg, BasicBlock, Instruction
from utility.transform import clean


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
        clean(func)
    return program


def dce_v2(program):
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
        clean(func)
    return program


if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads("".join(sys.stdin.readlines()))
    print(json.dumps(dce_v2(program)))
