import sys
import json
from utility.cfg import construct_cfg, BasicBlock, Instruction
from utility.lvn import LVNTable
from utility.transform import clean

def analyze(func):
    bbs: dict[str, BasicBlock] = construct_cfg(func)
    pass

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
