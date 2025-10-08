import sys
import json
from utility.cfg import CFG, PhiInstruction, Instruction, BasicBlock
from utility.transform import clean


# copied from https://github.com/sampsyo/bril/blob/main/examples/is_ssa.py
def is_ssa(bril):
    """Check whether a Bril program is in SSA form.

    Every function in the program may assign to each variable once.
    """
    for func in bril["functions"]:
        assigned = set()
        for instr in func["instrs"]:
            if "dest" in instr:
                if instr["dest"] in assigned:
                    return False
                else:
                    assigned.add(instr["dest"])
    return True


def insert_at_end(inst, bb: BasicBlock, cfg: CFG):
    if len(bb.instr_nodes) > 0:
        # ctrl flow op will not be invalidated
        if bb.instr_nodes[-1].val.instr is not None:
            last_op = bb.instr_nodes[-1].val.instr["op"]
            if last_op in {"br", "jmp", "ret"}:
                if len(bb.instr_nodes) == 1:
                    node_ = cfg.inst_list.insert_after(bb.label_instr_node, inst)
                else:
                    node_ = cfg.inst_list.insert_after(bb.instr_nodes[-2], inst)
                bb.instr_nodes.insert(-1, node_)
                return
        node_ = cfg.inst_list.insert_after(bb.instr_nodes[-1], inst)
    elif bb.label_instr_node is not None:
        node_ = cfg.inst_list.insert_after(bb.label_instr_node, inst)
    else:
        raise RuntimeError("Fail to resolve")
    bb.instr_nodes.append(node_)


def to_ssa(func, update_func=True):
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
            if bb.label == cfg.entry_name and "args" in func:
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
    # BFS on the dom tree
    work_list = [cfg.dom_tree[cfg.entry_name]]
    while len(work_list) > 0:
        node = work_list[0]
        work_list = work_list[1:]
        bb = cfg.bbs[node.bb_label]
        bb.rename_map = {}
        if node.bb_label == cfg.entry_name:
            if "args" in func:
                for arg in func["args"]:
                    bb.rename_map[arg["name"]] = arg["name"]
        else:
            bb.rename_map.update(cfg.bbs[node.parent.bb_label].rename_map)

        for instr_node in bb.instr_nodes:
            instr = instr_node.val
            # rename use
            if "args" in instr.instr:
                for idx, arg in enumerate(instr.instr["args"]):
                    # print(arg, bb.rename_map[arg])
                    instr.instr["args"][idx] = bb.rename_map[arg]
            # rename def and update map
            if "dest" in instr.instr:
                org_name = instr.instr["dest"]
                new_name = f"{org_name}_{name_cnt}"
                name_cnt += 1
                instr.instr["dest"] = new_name
                bb.rename_map[org_name] = new_name

        work_list.extend(node.children)

    # rename phi values
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
                    node_ = insert_at_end(
                        Instruction(undef_inst, -1), cfg.bbs[prec], cfg
                    )
                    cfg.bbs[prec].rename_map[org_name] = new_name
                phi.add_value(prec, cfg.bbs[prec].rename_map[org_name])

    if update_func:
        cfg.update_func_inst()

    return cfg


def eliminate_phi_in_ssa(cfg: CFG):
    for bb in cfg.bbs.values():
        for phi in bb.phi_instrs.values():
            var_name = phi.instr["dest"]
            # set
            for val, label in zip(phi.instr["args"], phi.instr["labels"]):
                prev = cfg.bbs[label]
                set_inst = {"args": [var_name, val], "op": "set"}
                insert_at_end(Instruction(set_inst, -1), prev, cfg)
            # get
            phi.instr["op"] = "get"
            phi.instr.pop("labels")
            phi.instr.pop("args")

    cfg.update_func_inst()


def eliminate_phi_out_ssa(cfg: CFG):
    for bb in cfg.bbs.values():
        for phi in bb.phi_instrs.values():
            var_name = phi.instr["dest"]
            var_type = phi.instr["type"]
            for val, label in zip(phi.instr["args"], phi.instr["labels"]):
                prev = cfg.bbs[label]
                id_inst = {
                    "args": [val],
                    "dest": var_name,
                    "op": "id",
                    "type": var_type,
                }
                insert_at_end(Instruction(id_inst, -1), prev, cfg)
            # get
            phi.instr = None
    cfg.update_func_inst()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads("".join(sys.stdin.readlines()))

    SSA = True
    for func in program["functions"]:
        cfg = to_ssa(func, False)
        if SSA:
            eliminate_phi_in_ssa(cfg)
        else:
            eliminate_phi_out_ssa(cfg)
            clean(func)
    # assert is_ssa(program)
    print(json.dumps(program))
