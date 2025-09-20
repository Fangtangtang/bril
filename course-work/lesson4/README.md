# Lesson4
## Constant propagation
In this task, I implemented constant propagation using the data-flow analysis framework.

[[ref]: pseudocode for solving a forward data flow problem with a worklist algorithm](https://www.cs.cornell.edu/courses/cs6120/2025fa/lesson/4/)
```txt
in[entry] = init
out[*] = init

worklist = all blocks
while worklist is not empty:
    b = pick any block from worklist
    in[b] = merge(out[p] for every predecessor p of b)
    out[b] = transfer(b, in[b])
    if out[b] changed:
        worklist += successors of b
```

Then, I integrated constant propagation with local value numbering (LVN) and dead code elimination (DCE) from Lesson 3 to further optimize the code.

### Some Details
- During the **merge** step, a variable `v` should only be added into `in[b]` if *all* predecessors’ `out[p]` mappings assign `v` to the **same constant value**. If the values differ across predecessors, or if any predecessor’s `out[p]` does not contain `v`, then `v` should **not** be propagated into `in[b]`.

- When integrating constant propagation into local value numbering (LVN), we should use the **final stabilized results** from constant propagation as additional information when constructing the LVN table.


### Case Study
To better illustrate the effect of constant propagation, consider the following example program.

**Original source code**:
```txt
# total_dyn_inst: 10
@main {
    a: int = const -100;
    b: int = const 6;
    q: int = div a b;
    sub_ : int = mul q b;
    remainder: int = sub a sub_;
    zero: int = const 0;
    flag: bool = ge remainder zero;
    br flag .end .adjust;
.adjust:
    remainder: int = add remainder b;
.end:
    print remainder; 
}
```
This results in 10 dynamic instructions being executed.

**After applying LVN (with constant folding) and DCE**:
```txt
# total_dyn_inst: 5
@main {
  b: int = const 6;
  remainder: int = const 2;
  flag: bool = const true;
  br flag .end .adjust;
.adjust:
  remainder: int = add remainder b;
.end:
  print remainder;
}
```
- Local value numbering detects that several computations are redundant, and dead code elimination removes unused variables such as a, q, and zero.

- The program now computes directly that the initial remainder is 2 and the branch condition flag is always true.

This reduces the total dynamic instruction count to 5

**After integrating constant propagation**:
```txt
# total_dyn_inst: 4
@main {
  remainder: int = const 2;
  flag: bool = const true;
  br flag .end .adjust;
.adjust:
  remainder: int = const 8;
.end:
  print remainder;
}
```
- Constant propagation goes one step further, it substitutes constant values through the control flow, simplifying computations across basic blocks. For example, in the .adjust block, remainder is directly folded into 8 rather than recomputed via add remainder b.

This further reduces the dynamic instruction count to 4.
