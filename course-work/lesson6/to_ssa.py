import sys
import json
from utility.cfg import CFG, PhiInstruction, Instruction, ENTRY_NAME


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
            # function arguments are also 'def'
            if bb.label == ENTRY_NAME:
                for arg in func["args"]:
                    defs[arg["name"]] = arg["type"]
            for phi_name, phi in bb.phi_instrs.items():
                defs[phi_name] = phi.instr["type"]
            for instr_node in bb.instr_nodes:
                instr = instr_node.val.instr
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
                        if len(cfg.bbs[dom_frontier].instr_nodes) > 0:
                            node_ = cfg.inst_list.insert_before(
                                cfg.bbs[dom_frontier].instr_nodes[0],
                                cfg.bbs[dom_frontier].phi_instrs[new_def],
                            )
                        elif cfg.bbs[dom_frontier].label_instr_node is not None:
                            node_ = cfg.inst_list.insert_after(
                                cfg.bbs[dom_frontier].label_instr_node,
                                cfg.bbs[dom_frontier].phi_instrs[new_def],
                            )
                        else:
                            raise RuntimeError("Fail to resolve")
                        cfg.bbs[dom_frontier].instr_nodes.insert(0, node_)

    name_cnt = 0
    # step 2: rename
    for bb in cfg.bbs.values():
        # org name -> rename
        bb.rename_map = {}
        # get defs
        for org_name, phi in bb.phi_instrs.items():
            new_name = f"{org_name}_{name_cnt}"
            name_cnt += 1
            bb.rename_map[org_name] = new_name
            phi.instr["dest"] = new_name
        for instr_node in bb.instr_nodes:
            instr = instr_node.val
            # rename use
            if "args" in instr.instr:
                for idx, arg in enumerate(instr.instr["args"]):
                    instr.instr["args"][idx] = bb.rename_map[arg]
            # rename def and update map
            if "dest" in instr.instr:
                org_name = instr.instr["dest"]
                new_name = f"{org_name}_{name_cnt}"
                name_cnt += 1
                instr.instr["dest"] = new_name
                bb.rename_map[org_name] = new_name
    for bb in cfg.bbs.values():
        for org_name, phi in bb.phi_instrs.items():
            for prec in bb.precursors:
                if org_name not in cfg.bbs[prec].rename_map:
                    # insert variable def placeholder in prec
                    new_name = f"{org_name}_{name_cnt}"
                    name_cnt += 1
                    undef_inst = {
                        "dest": new_name,
                        "op": "undef",
                        "type": phi.instr["type"],
                    }
                    if len(cfg.bbs[prec].instr_nodes) > 0:
                        node_ = cfg.inst_list.insert_after(
                            cfg.bbs[prec].instr_nodes[-1], Instruction(undef_inst, -1)
                        )
                    elif cfg.bbs[prec].label_instr_node is not None:
                        node_ = cfg.inst_list.insert_before(
                            cfg.bbs[prec].label_instr_node, Instruction(undef_inst, -1)
                        )
                    else:
                        raise RuntimeError("Fail to resolve")
                    cfg.bbs[prec].instr_nodes.append(node_)
                    cfg.bbs[prec].rename_map[org_name] = new_name
                phi.add_value(prec, cfg.bbs[prec].rename_map[org_name])

    cfg.update_func_inst()


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
    print(json.dumps(program))
