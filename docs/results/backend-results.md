# Backend results

This page summarizes the current CPU↔GPU comparison results that are generated from the repository.

## Short benchmark

![](../assets/generated/backend/benchmark_runtime.png)

| Grid | CPU (s) | GPU (s) |
|---|---:|---:|
| 64² | 0.445 | 0.265 |
| 128² | 0.824 | 0.120 |
| 256² | 15.716 | 0.227 |

## Manuscript-scale backend validation

![](../assets/generated/backend/manuscript_runtime.png)

| Case | CPU (s) | GPU (s) |
|---|---:|---:|
| Taylor–Green | 0.194 | 0.122 |
| Default vortex array | 12.706 | 5.584 |
| Pseudo-turbulence 256² | 276.447 | 20.130 |

Representative maximum relative errors from `manuscript_gpu_validation.json` remain extremely small and support close CPU↔GPU agreement in double precision.
