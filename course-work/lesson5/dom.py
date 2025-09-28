import sys
import json
from utility.cfg import CFG, BasicBlock, ENTRY_NAME


def get_dom(cfg: CFG):
    doms: dict[str, set[str]] = {
        bb_label: set(cfg.bbs.keys()) for bb_label in cfg.bbs.keys()
    }
    update = True
    # [NOTE]: iterate over the CFG in reverse post-order for efficiency
    ordered_labels = cfg.reverse_post_order()
    while update:
        update = False
        for bb_label in ordered_labels:
            new_doms = {bb_label}
            if len(cfg.bbs[bb_label].precursors) > 0:
                new_doms |= set.intersection(
                    *(doms[pred] for pred in cfg.bbs[bb_label].precursors)
                )
            if new_doms != doms[bb_label]:
                doms[bb_label] = new_doms
                update = True
    return doms


# naive version
def build_dom_tree(cfg: CFG):
    doms: dict[str, set[str]] = get_dom(cfg)
    # entry has no immediately dominator
    imm_doms: dict[str, str] = {ENTRY_NAME: None}
    for bb_label, dom in doms.items():
        if bb_label == ENTRY_NAME:
            continue
        candidates = dom - {bb_label}
        imm_dom = None
        for c in candidates:
            if all(c == other or c not in doms[other] for other in candidates):
                imm_dom = c
                break
        imm_doms[bb_label] = imm_dom
    # build dom tree
    dom_tree: dict[str, list[str]] = {b: [] for b in doms.keys()}
    for bb_label, imm_dom in imm_doms.items():
        if imm_dom is not None:
            dom_tree[bb_label].append(imm_dom)
    return imm_doms


class DomNode:
    def __init__(self, name, depth, parent: "DomNode"):
        self.bb_label = name
        self.depth = depth
        self.parent = parent
        self.children: list["DomNode"] = []


def build_dom_tree_eff(cfg: CFG):
    ordered_labels = cfg.topological_order()

    def lca(node1: DomNode, node2: DomNode):
        while node1.depth > node2.depth:
            node1 = node1.parent
        while node2.depth > node1.depth:
            node2 = node2.parent
        while node1 != node2:
            node1 = node1.parent
            node2 = node2.parent
        return node1

    dom_tree: dict[str, DomNode] = {}
    for bb_label in ordered_labels:
        if bb_label == ENTRY_NAME:
            dom_tree[ENTRY_NAME] = DomNode(ENTRY_NAME, 0, None)
        else:
            if len(cfg.dag_bbs[bb_label].precursors) == 0:
                continue
            dom = None
            for pred in cfg.dag_bbs[bb_label].precursors:
                if dom is None:
                    dom = dom_tree[pred]
                else:
                    dom = lca(dom, dom_tree[pred])
            dom_tree[bb_label] = DomNode(bb_label, dom.depth + 1, dom)

    imm_doms: dict[str, str] = {ENTRY_NAME: None}
    for name, node in dom_tree.items():
        if name != ENTRY_NAME:
            imm_doms[name] = node.parent.bb_label
    return imm_doms


def get_dom_frontier(cfg: CFG, imm_doms: dict[str, str]):
    dom_frontier: dict[str, set[str]] = {name: set() for name in imm_doms.keys()}

    for name in cfg.bbs.keys():
        bb = cfg.bbs[name]
        if len(bb.precursors) >= 2:
            for pred in bb.precursors:
                runner = pred
                while runner != imm_doms[bb.label]:
                    dom_frontier[runner].add(bb.label)
                    runner = imm_doms[runner]


def check_dom(bbs: dict[str, BasicBlock]):
    minimal_paths: list[list[str]] = []

    def get_path(current_path: list[str]):
        current_bb = current_path[-1]
        minimal_paths.append(current_path)
        if bbs[current_bb].successors is not None:
            for suc in bbs[current_bb].successors:
                if not suc in current_path:
                    new_path = current_path.copy()
                    new_path.append(suc)
                    get_path(new_path)

    get_path([ENTRY_NAME])
    sample_doms: dict[str, set[str]] = {
        bb_label: set(bbs.keys()) for bb_label in bbs.keys()
    }
    for path in minimal_paths:
        for i in range(len(path)):
            sample_doms[path[i]] = set.intersection(
                sample_doms[path[i]], (set(path[: i + 1]))
            )
    return sample_doms


if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads("".join(sys.stdin.readlines()))
    for func in program["functions"]:
        cfg = CFG(func)

        # dom
        dom = get_dom(cfg)
        sample = check_dom(cfg.bbs)
        assert dom == sample

        # immediately dominates
        idoms = build_dom_tree_eff(cfg)
        sample_idoms = build_dom_tree(cfg)
        assert idoms == sample_idoms

        # dominance frontier
        get_dom_frontier(cfg, idoms)

    print(json.dumps(program))
