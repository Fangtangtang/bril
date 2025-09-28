import sys
import json
import copy
from collections import deque

ENTRY_NAME = "entry"


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
    bb = BasicBlock(ENTRY_NAME)
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
    bfs_list.append(block_map[ENTRY_NAME])
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


class CFG:
    def __init__(self, func, construct_dag=False):
        self.bbs: dict[str, BasicBlock] = construct_cfg(func)
        if construct_dag:
            self.construct_dag()
        else:
            self.dag_bbs: dict[str, BasicBlock] = None

    def construct_dag(self):
        self.dag_bbs: dict[str, BasicBlock] = copy.deepcopy(self.bbs)

        def analysis_path(current_path: list[str]):
            current_bb = current_path[-1]
            if self.bbs[current_bb].successors is not None:
                for suc in self.bbs[current_bb].successors:
                    if not suc in current_path:
                        new_path = current_path.copy()
                        new_path.append(suc)
                        analysis_path(new_path)
                    else:
                        if suc in self.dag_bbs[current_bb].successors:
                            self.dag_bbs[current_bb].successors.remove(suc)
                        if current_bb in self.dag_bbs[suc].precursors:
                            self.dag_bbs[suc].precursors.remove(current_bb)

        analysis_path([ENTRY_NAME])

    # TODO: parse from dumped file

    def reverse_post_order(self):
        # (shihan): it construct a DFS tree and give the index order
        visited = set()
        order = []

        def dfs_post_order(bb_label):
            if bb_label in visited:
                return
            visited.add(bb_label)
            if self.bbs[bb_label].successors is not None:
                for suc in self.bbs[bb_label].successors:
                    dfs_post_order(suc)
            order.append(bb_label)

        dfs_post_order(ENTRY_NAME)
        return list(reversed(order))

    def topological_order(self):
        if self.dag_bbs is None:
            self.construct_dag()
        order = [ENTRY_NAME]
        while len(order) < len(self.dag_bbs):
            for bb_label, bb in self.dag_bbs.items():
                if bb_label in order:
                    continue
                if all(pred in order for pred in bb.precursors):
                    order.append(bb_label)
        return order

    # TODO: dump CFG


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
