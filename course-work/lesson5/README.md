# Lesson 5
## Dominance
- `A` dominates `B` iff all paths from the entry to `B` include `A`.
- The dominator tree is a convenient data structure for storing the dominance relationships in an entire function. The recursive children of a given node in a tree are the nodes that that node dominates.
- `A` **strictly dominates** `B` iff `A` dominates `B` and `A` ≠ `B`.
- `A` **immediately dominates** `B` iff `A` dominates `B` but `A` does not strictly dominate any other node that strictly dominates `B`. (In which case `A` is `B`’s direct parent in the dominator tree.)
- A **dominance frontier** is the set of nodes that are just “one edge away” from being dominated by a given node. Put differently, `A`’s dominance frontier contains `B` iff `A` does not strictly dominate `B`, but `A` does dominate some predecessor of `B`.

