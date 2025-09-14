import os
import re
import csv


def extract_total_dyn_inst(filepath):
    pattern = re.compile(r"total_dyn_inst:\s*(\d+)")
    with open(filepath, "r") as f:
        for line in f:
            m = pattern.search(line)
            if m:
                return int(m.group(1))
    return None


def main(directory, output_csv="results.csv"):
    data = {}
    for root, _, files in os.walk(directory):
        for fname in files:
            if fname.endswith(".bril"):
                base = fname.rsplit(".", 1)[0]
                print(base)
                try:
                    baseline_filepath = os.path.join(root, f"{base}.prof")
                    baseline_val = extract_total_dyn_inst(baseline_filepath)
                    opt_filepath = os.path.join(root, f"{base}.bril.log")
                    dce_val = extract_total_dyn_inst(opt_filepath)
                except:
                    continue
                data[base] = {}
                data[base]["baseline"] = baseline_val
                data[base]["dce"] = dce_val

    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Name", "baseline", "dce"])
        for name, vals in data.items():
            writer.writerow([name, vals["baseline"], vals["dce"]])


if __name__ == "__main__":
    main("../../benchmarks", "results1.csv")
