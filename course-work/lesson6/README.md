# Lesson 6
```bash
turnt -e ssa */*.bril
```

### Implementation

For the “into SSA” transformation, I implemented the **dominance-frontier-based algorithm**, which consists of two main phases: iterative φ-insertion and variable renaming.
One important implementation detail is that function parameters should be treated as definitions within the 'entry basic block', ensuring all uses in the function body have a corresponding reaching definition.


For the “out of SSA” transformation, I lowered φ-instructions by splitting them into `id` operations within their respective predecessor blocks.

To simplify instruction-level insertions and deletions during this process, I implemented a lightweight linked list structure to manage instructions within each function, allowing efficient and flexible transformations.


### Correctness Verification

I tested both transformations across the full bril benchmark suite:

* The into SSA pass was validated using the provided `is_ssa.py` checker to confirm that the transformed program satisfies the SSA property.
* Both transformations were verified for correctness by comparing program outputs before and after the transformation.

### Overhead Measurement

To measure the transformation overhead, I compared the dynamic instruction count between the original, ssa and round-tripped programs.
Results show:

| Transformation | Max Overhead | Average Overhead |
| -------------- | ------------ | ---------------- |
| Into SSA       | 4.63×        | 2.17×            |
| Round-tripped  | 2.82×        | 1.63×            |

The figure below summarizes the detailed dynamic instruction counts across all benchmarks.

<img width="818" height="246" alt="image" src="https://github.com/user-attachments/assets/eade2211-4960-435d-b390-9e806c72c22a" />
