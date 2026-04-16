# Benchmark performance

Use this guide to measure CPU or GPU runtime over several grid sizes.

## Benchmark the CPU backend

```bash
nslab2d benchmark --backend cpu --N 64,128,256 --dt 0.1,0.1,0.05 --simutime-seconds 1
```

## Benchmark the GPU backend

```bash
nslab2d benchmark --backend gpu --N 64,128,256 --dt 0.1,0.1,0.05 --simutime-seconds 1
```

## Interpret the results

The command returns structured JSON entries containing:

- backend
- grid size `N`
- time step `dt`
- simulated physical time
- elapsed wall-clock time

Use the same `(N, dt, simutime_seconds)` combinations for fair comparison.

## Related pages

- [Compare CPU and GPU on the same case](../tutorials/compare-cpu-and-gpu.md)
- [Backend results](../results/backend-results.md)
- [CLI reference](../reference/cli-reference.md)
