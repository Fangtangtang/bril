import sys
import json
from utility.cfg import CFG, PhiInstruction


def to_ssa(func):
    cfg = CFG(func)
    cfg.build_dom()

    # step 1: insert Phi
    update = True
    while update:
        update = False
        for bb in cfg.bbs.values():
            # name -> type
            defs: dict[str, str] = {}
            for phi_name, phi in bb.phi_instrs.items():
                defs[phi_name] = phi.instr["type"]
            for instr in bb.instr_nodes:
                if "dest" in instr:
                    assert "type" in instr
                    defs[instr["dest"]] = instr["type"]
            for dom_frontier in cfg.dom_frontier[bb.label]:
                for new_def, new_def_type in defs.items():
                    if new_def not in cfg.bbs[dom_frontier].phi_instrs:
                        update = True
                        cfg.bbs[dom_frontier].phi_instrs[new_def] = PhiInstruction(
                            new_def, new_def_type
                        )

    name_cnt = 0
    # step 2: rename
    for bb in cfg.bbs.values():
        # org name -> rename
        bb.val_map = {}
        # get defs
        for org_name, phi in bb.phi_instrs.items():
            new_name = f"{org_name}_{name_cnt}"
            name_cnt += 1
            bb.val_map[org_name] = new_name
            phi.instr["dest"] = new_name
        for instr in bb.instr_nodes:
            # rename use
            if "args" in instr.instr:
                for idx, arg in instr.instr["args"]:
                    instr.instr["args"][idx] = bb.val_map[arg]
            # rename def and update map
            if "dest" in instr.instr:
                org_name = instr.instr["dest"]
                new_name = f"{org_name}_{name_cnt}"
                name_cnt += 1
                instr.instr["dest"] = new_name
                bb.val_map[org_name] = new_name
    for bb in cfg.bbs.values():
        for org_name, phi in bb.phi_instrs.items():
            for prec in bb.precursors:
                if org_name in cfg.bbs[prec].val_map:
                    phi.add_value(prec, cfg.bbs[prec].val_map[org_name])
                else:
                    # insert variable def placeholder in prec
                    cfg.bbs[prec].instr_nodes


if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads("".join(sys.stdin.readlines()))
    for func in program["functions"]:
        to_ssa(func)
