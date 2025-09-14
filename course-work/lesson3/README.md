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
