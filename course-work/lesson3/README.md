# Lesson3
## Algorithms
**Local Value Numbering (LVN):**
LVN is applied to each basic block to detect redundant computations and reuse existing values. To avoid naming conflicts, variables defined within a block are renamed so that their names remain distinct. For correctness across basic blocks, the last definition of a 'live-out' variable is preserved with its original name. 
In addition, simple optimizations such as reordering the operands of commutative operations are applied to expose more redundancy.

**Dead Code Elimination (DCE):**
DCE removes instructions whose results are never used in the function. This includes eliminating instructions that are overwritten before their value is used (local), and instructions that define values unused throughout the entire function (global).


LVN can serve as a preprocessing pass to DCE, since eliminating redundant computations often enables further removal of dead code.

## Evaluation
I tested and evaluated the algorithm on the [bril benchmark suite](https://github.com/sampsyo/bril/tree/main/benchmarks) (commit `c96fa8e2f7190c31ebb6bd10e54eb49e277df663`). The implementation was able to correctly optimize all test cases under `core`, `float`, and `long`. 
(For the other cases, the local value numbering algorithm may fail mainly because I haven't deal with cases using pointers.)

On the `core` benchmarks, DCE alone optimized 17/55 cases, while LVN combined with DCE optimized 21/55 cases. 
The figure below shows the normalized dynamic instruction count of these 21 optimized cases. The baseline represents execution without any optimization, while DCE applies dead code elimination, and LVN+DCE applies local value numbering as a preprocessing step before dead code elimination.
<img width="676" height="308" alt="image" src="https://github.com/user-attachments/assets/728cb304-b662-4395-af5e-74f63dd0878f" />

## Cmd Notes

```txt
[envs.dce]
default = false
command = "bril2json < {filename} | python3 ../course-work/lesson3/dce.py | brili -p {args} 2> {filename}.log"
output.out = "-"
```

under `benchmarks` run  
```bash
turnt -e dce */*.bril
```
