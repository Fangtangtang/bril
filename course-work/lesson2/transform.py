import sys
import json


def transform(program):
    for func in program["functions"]:
        for inst in func["instrs"]:
            if "op" in inst and inst["op"] == "print" and len(inst["args"]) == 1:
                inst["args"] = [inst["args"][0], inst["args"][0]]

    return program


if __name__ == "__main__":
    assert len(sys.argv) == 2
    with open(sys.argv[1], "r") as file:
        program = json.load(file)
    print(json.dumps(transform(program)))
