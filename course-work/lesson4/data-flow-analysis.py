import sys
import json
from collections import deque

from utility.cfg import construct_cfg, BasicBlock
from utility.lvn import Const, run_lvn
from utility.transform import clean
from lesson3.dce import dce_v2


def analyze(func):
    bbs: dict[str, BasicBlock] = construct_cfg(func)
    work_list = deque()
    const_out: dict[str, dict[str, Const]] = {}
    for name, bb in bbs.items():
        run_lvn(bb)
        work_list.append(bb)
        const_out[name] = {}
    while work_list:

        def get_const_in(basic_block):
            prec_outs = [const_out[prec] for prec in basic_block.precursors]
            if prec_outs:
                key_intersection = set(prec_outs[0].keys())
                for d in prec_outs[1:]:
                    key_intersection &= set(d.keys())
            else:
                key_intersection = set()
            const_in: dict[str, Const] = {
                var_name: None for var_name in key_intersection
            }
            for prec in basic_block.precursors:
                prec_out = const_out[prec]
                for var_name, val in const_in.items():
                    if val is None:
                        const_in[var_name] = prec_out[var_name]
                    elif val != prec_out[var_name]:
                        const_in.pop(var_name)
            return const_in

        task_bb: BasicBlock = work_list.popleft()
        const_in = get_const_in(task_bb)
        for instr in task_bb.instrs:
            if "dest" in instr.instr:
                dest = instr.instr["dest"]
                if "op" in instr.instr:
                    op = instr.instr["op"]
                    if op == "const":
                        value = instr.instr["value"]
                        if instr.instr["type"] == "float":
                            value = float(value)
                        elif instr.instr["type"] == "bool":
                            value = bool(value)
                        const_in[dest] = Const(value)
                        continue
                if dest in const_in:
                    const_in.pop(dest)
        if const_out[task_bb.label] != const_in and task_bb.successors is not None:
            for suc in task_bb.successors:
                work_list.append(bbs[suc])
        const_out[task_bb.label] = const_in
    for bb in bbs.values():
        run_lvn(bb, get_const_in(bb))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads("".join(sys.stdin.readlines()))
    for func in program["functions"]:
        analyze(func)
    print(json.dumps(dce_v2(program)))
