import sys
import json
from collections import deque


class Instruction:
    def __init__(self, instr, idx):
        self.instr = instr
        self.idx = idx

    def __str__(self):
        return f"{self.idx}: {self.instr}"

    def __repr__(self):
        return self.__str__()


class BasicBlock:
    cnt = 0

    def __init__(self, label=None):
        self.idx = BasicBlock.cnt
        BasicBlock.cnt += 1
        self.label = label if label is not None else f"bb_{self.idx}"
        self.instrs: list[Instruction] = []
        self.precursors = set()
        self.successors = set()

    def __str__(self):
        return f"{self.label}: {len(self.instrs)}"

    def __repr__(self):
        return self.__str__()


def construct_cfg(func, verbose=False):
    if verbose:
        print(func["name"])
    block_map: dict[str, BasicBlock] = {}
    bb = BasicBlock("entry")
    for idx, inst in enumerate(func["instrs"]):
        if "label" in inst:
            block_map[bb.label] = bb
            if bb.successors is not None and len(bb.successors) == 0:
                bb.successors.add(inst["label"])
            bb = BasicBlock(inst["label"])
        elif "op" in inst:
            bb.instrs.append(Instruction(inst, idx))
            if inst["op"] == "br" or inst["op"] == "jmp":
                bb.successors.update(inst["labels"])
                block_map[bb.label] = bb
                bb = BasicBlock()
            elif inst["op"] == "ret":
                bb.successors = None
                block_map[bb.label] = bb
                bb = BasicBlock()
        else:
            raise ValueError("Unknown")
    block_map[bb.label] = bb
    for bb in block_map.values():
        if bb.successors is not None:
            for label in bb.successors:
                block_map[label].precursors.add(bb.label)

    # clean up
    clean_block_map = {}
    bfs_list = deque()
    bfs_list.append(block_map["entry"])
    while bfs_list:
        bb: BasicBlock = bfs_list.popleft()
        clean_block_map[bb.label] = bb
        if bb.successors is not None:
            for suc in bb.successors:
                if suc not in clean_block_map:
                    bfs_list.append(block_map[suc])
    for bb in clean_block_map.values():
        bb.precursors &= clean_block_map.keys()
        if bb.successors is not None:
            bb.successors &= clean_block_map.keys()

    if verbose:
        for bb in block_map.values():
            print(bb)
            print("\t", bb.precursors)
            print("\t", bb.successors)

    return clean_block_map


if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads("".join(sys.stdin.readlines()))
    for func in program["functions"]:
        bbs: dict[str, BasicBlock] = construct_cfg(func)
