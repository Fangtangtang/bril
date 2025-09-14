
def clean(func):
    """
    remove `None` placeholder in func["instrs"]
    """
    instrs = []
    for inst in func["instrs"]:
        if inst is not None:
            instrs.append(inst)
    func["instrs"] = instrs
