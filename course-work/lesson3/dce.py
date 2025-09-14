import sys
import json


def transform(program):
    for func in program["functions"]:
        updated = True
        while updated:
            updated = False
            used = set()
            for inst in func["instrs"]:
                if "args" in inst :
                    for arg in inst["args"]:
                        used.add(arg)
            instrs = []
            for inst in func["instrs"]:
                if "dest" in inst:
                    if inst["dest"] in used:
                        instrs.append(inst)
                else:
                    instrs.append(inst)
            func["instrs"] = instrs

    return program


if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads(''.join(sys.stdin.readlines())) 
    print(json.dumps(transform(program)))
