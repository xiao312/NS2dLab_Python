# Compare CPU and GPU on the same case

This tutorial shows how to run the same configuration on the CPU and GPU backends and compare the results.

## What you will do

You will:

1. check that a GPU is visible
2. run a short CPU↔GPU comparison case
3. inspect the reported numerical differences

Estimated time: 5 minutes.

## Prerequisites

- GPU dependencies installed; see [Installation](../start-here/installation.md)
- an NVIDIA GPU available to CuPy

## Step 1: inspect the device

Run:

```bash
nslab2d device-info
```

You should see whether GPU execution is available and, if so, device metadata.

## Step 2: compare backends on a short case

Run:

```bash
nslab2d compare-backends --N 64 --dt 0.1 --simutime-seconds 2
```

## Step 3: inspect the result

The command prints a JSON summary containing:

- the shared case configuration
- CPU elapsed time
- GPU elapsed time
- error metrics for:
  - `Ekin`
  - `Diss`
  - final `U`
  - final `V`

The relative errors should be very small when both backends are working correctly.

## What to notice

- the CPU backend is the reference backend
- exact bitwise identity is not required
- very small relative errors are expected in double precision
- timing differences become more favorable to the GPU as grid size increases

## Next steps

- [Benchmark performance across grid sizes](../how-to/benchmark-performance.md)
- [Review backend results](../results/backend-results.md)
- [Read the GPU backend explanation](../explanation/gpu-backend.md)
