import sys
import json


class BasicBlock:
    cnt = 0

    def __init__(self, label=None):
        self.idx = BasicBlock.cnt
        BasicBlock.cnt += 1
        self.label = label if label is not None else f"bb_{self.idx}"
        self.instrs = []
        self.precursors = set()
        self.successors = set()

    def __str__(self):
        return f"{self.label}: {len(self.instrs)}"

    def __repr__(self):
        return self.__str__()


def construct_cfg(func):
    print(func["name"])
    block_map: dict[str, BasicBlock] = {}
    bb = BasicBlock("entry")
    for inst in func["instrs"]:
        if "label" in inst:
            block_map[bb.label] = bb
            if bb.successors is not None and len(bb.successors) == 0:
                bb.successors.add(inst["label"])
            bb = BasicBlock(inst["label"])
        elif "op" in inst:
            bb.instrs.append(inst)
            if inst["op"] == "br" or inst["op"] == "jmp":
                bb.successors.update(inst["labels"])
            elif inst["op"] == "ret":
                bb.successors = None
        else:
            raise ValueError("Unknown")
    block_map[bb.label] = bb
    for bb in block_map.values():
        if bb.successors is not None:
            for label in bb.successors:
                block_map[label].precursors.add(bb.label)

    for bb in block_map.values():
        print(bb)
        print("\t", bb.precursors)
        print("\t", bb.successors)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads("".join(sys.stdin.readlines()))
    for func in program["functions"]:
        construct_cfg(func)
