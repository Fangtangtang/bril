# Analyzer
Some tools for program analyze.


```txt
clang --version

clang version 20.0.0git (https://github.com/llvm/llvm-project.git fbec1c2a08ce2ae9750ddf3cecc86c5dd2bbc9d8)
Target: x86_64-unknown-linux-gnu
Thread model: posix
```

## A simple loop iterator analyzer

For the example in `tests/t1.c`
```txt

=====================
Found loop iterator   %i = alloca i32, align 4
        increase by 1 bounded to 10.
The condition is:         %cmp = icmp slt i32 %0, 10
=====================

=====================
Found loop iterator   %i1 = alloca i32, align 4
        increase by -1 bounded to 0.
The condition is:         %cmp3 = icmp sgt i32 %4, 0
=====================
```