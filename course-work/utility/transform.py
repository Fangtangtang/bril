def clean(func):
    """
    remove `None` placeholder in func["instrs"]
    """
    instrs = []
    for inst in func["instrs"]:
        if inst is not None:
            instrs.append(inst)
    if len(func["instrs"]) == len(instrs):
        return False
    func["instrs"] = instrs
    return True
