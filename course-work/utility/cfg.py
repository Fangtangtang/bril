import sys
import json
import copy
from collections import deque
from .ds import LinkedList, ListNode

ENTRY_NAME = "entry"


class Instruction:
    def __init__(self, instr, idx):
        self.instr = instr
        self.idx = idx

    def __str__(self):
        return f"{self.idx}: {self.instr}"

    def __repr__(self):
        return self.__str__()


class PhiInstruction(Instruction):
    def __init__(self, new_def, new_def_type):
        phi = {
            "args": [],
            "dest": new_def,
            "op": "phi",
            "type": new_def_type,
        }
        super().__init__(phi, -1)
        # bb label -> variable name
        self.label2value: dict[str, str] = {}

    def add_value(self, label, var):
        self.label2value[label] = var
        self.instr["args"].append(var)
        self.instr["args"].append(label)


class BasicBlock:
    cnt = 0

    def __init__(self, label=None, label_instr_node=None):
        self.idx = BasicBlock.cnt
        BasicBlock.cnt += 1
        self.label = label if label is not None else f"bb_{self.idx}"
        self.phi_instrs: dict[str, PhiInstruction] = {}
        self.label_instr_node: ListNode[Instruction] = label_instr_node
        self.instr_nodes: list[ListNode[Instruction]] = []
        self.precursors = set()
        self.successors = set()

        self.val_map: dict[str, str] = None

    def __str__(self):
        return f"{self.label}: {len(self.instr_nodes)}"

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
            bb.instr_nodes.append(Instruction(inst, idx))
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
    class DomNode:
        def __init__(self, name, depth, parent: "CFG.DomNode"):
            self.bb_label = name
            self.depth = depth
            self.parent = parent
            self.children: list["CFG.DomNode"] = []

    def __init__(self, func, construct_dag=False):
        self.func = func
        self.inst_list: LinkedList[Instruction] = LinkedList[Instruction]()
        instrs: list[Instruction] = []
        for idx, inst in enumerate(self.func["instrs"]):
            instrs.append(Instruction(inst, idx))
        link_node_list: list[ListNode[Instruction]] = self.inst_list.list_to_linked(
            val_list=instrs
        )
        # build cfg
        self.bbs: dict[str, BasicBlock] = {}
        block_map: dict[str, BasicBlock] = {}
        bb = BasicBlock(ENTRY_NAME)
        for idx, node in enumerate(link_node_list):
            inst = node.val.instr
            if "label" in inst:
                block_map[bb.label] = bb
                if bb.successors is not None and len(bb.successors) == 0:
                    bb.successors.add(inst["label"])
                bb = BasicBlock(inst["label"], node)
            elif "op" in inst:
                bb.instr_nodes.append(node)
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
        bfs_list = deque()
        bfs_list.append(block_map[ENTRY_NAME])
        while bfs_list:
            bb: BasicBlock = bfs_list.popleft()
            self.bbs[bb.label] = bb
            if bb.successors is not None:
                for suc in bb.successors:
                    if suc not in self.bbs:
                        bfs_list.append(block_map[suc])
        for bb in self.bbs.values():
            bb.precursors &= self.bbs.keys()
            if bb.successors is not None:
                bb.successors &= self.bbs.keys()

        self.dom_tree: dict[str, CFG.DomNode] = None
        self.dom_frontier: dict[str, set[str]] = None
        if construct_dag:
            self.construct_dag()
        else:
            self.dag_bbs: dict[str, BasicBlock] = None

    def construct_dag(self):
        self.dag_bbs: dict[str, BasicBlock] = {}
        for bb_label, real_bb in self.bbs.items():
            fake_bb = BasicBlock(bb_label)
            fake_bb.precursors.update(real_bb.precursors)
            if real_bb.successors is None:
                fake_bb.successors = None
            else:
                fake_bb.successors.update(real_bb.successors)
            self.dag_bbs[bb_label] = fake_bb

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

    def build_dom(self):
        if self.dom_tree is not None:
            return

        ordered_labels = self.topological_order()

        def lca(node1: CFG.DomNode, node2: CFG.DomNode):
            while node1.depth > node2.depth:
                node1 = node1.parent
            while node2.depth > node1.depth:
                node2 = node2.parent
            while node1 != node2:
                node1 = node1.parent
                node2 = node2.parent
            return node1

        self.dom_tree: dict[str, CFG.DomNode] = {}
        for bb_label in ordered_labels:
            if bb_label == ENTRY_NAME:
                self.dom_tree[ENTRY_NAME] = CFG.DomNode(ENTRY_NAME, 0, None)
            else:
                if len(self.dag_bbs[bb_label].precursors) == 0:
                    continue
                dom = None
                for pred in self.dag_bbs[bb_label].precursors:
                    if dom is None:
                        dom = self.dom_tree[pred]
                    else:
                        dom = lca(dom, self.dom_tree[pred])
                self.dom_tree[bb_label] = CFG.DomNode(bb_label, dom.depth + 1, dom)

        imm_doms: dict[str, str] = {ENTRY_NAME: None}
        for name, node in self.dom_tree.items():
            if name != ENTRY_NAME:
                imm_doms[name] = node.parent.bb_label

        self.dom_frontier: dict[str, set[str]] = {
            name: set() for name in imm_doms.keys()
        }

        for name in self.bbs.keys():
            bb = self.bbs[name]
            if len(bb.precursors) >= 2:
                for pred in bb.precursors:
                    runner = pred
                    while runner != imm_doms[bb.label]:
                        self.dom_frontier[runner].add(bb.label)
                        runner = imm_doms[runner]

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
