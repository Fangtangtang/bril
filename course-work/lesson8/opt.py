import sys
import json
from utility.cfg import CFG

def opt(func):
    cfg = CFG(func)
    cfg.dump("tests")
    cfg.build_dom()
    cfg.find_natural_loop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert len(sys.argv) == 2
        with open(sys.argv[1], "r") as file:
            program = json.load(file)
    else:
        # json from stdin
        program = json.loads("".join(sys.stdin.readlines()))
    for func in program["functions"]:
        opt(func)
