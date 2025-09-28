import sys
import json
from utility.cfg import construct_cfg, BasicBlock, ENTRY_NAME


def get_dom(bbs: dict[str, BasicBlock]):
    doms: dict[str, set[str]] = {bb_label: set(bbs.keys()) for bb_label in bbs.keys()}
    update = True
    while update:
        update = False
        for bb_label, bb in bbs.items():
            new_doms = {bb_label}
            if len(bb.precursors) > 0:
                new_doms |= set.intersection(*(doms[pred] for pred in bb.precursors))
            if new_doms != doms[bb_label]:
                doms[bb_label] = new_doms
                update = True
    return doms


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
        bbs: dict[str, BasicBlock] = construct_cfg(func)
        dom = get_dom(bbs)
        sample = check_dom(bbs)
        assert dom == sample
    print(json.dumps(program))