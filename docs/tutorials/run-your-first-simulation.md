# Run your first simulation

This tutorial walks you through the smallest meaningful NS2dLab workflow: running a short CPU simulation and inspecting the saved output.

## What you will do

In this tutorial, you will:

1. run a short 2D NS2dLab case on the CPU
2. save MATLAB-style timeseries output
3. save the final velocity field as an `.npz` snapshot
4. learn what files were created

Estimated time: 5–10 minutes.

## Prerequisites

- the package is installed; see [Installation](../start-here/installation.md)
- you are in the repository root with the virtual environment activated

## Step 1: run a short case

Run:

```bash
nslab2d run \
  --backend cpu \
  --N 128 \
  --dt 0.1 \
  --simutime-seconds 10 \
  --output results/VortexArray2d_128.mat \
  --save-field-npz results/VortexArray2d_128_field.npz
```

## Step 2: inspect the command output

You should see a small JSON summary describing:

- the case name
- the backend used
- elapsed wall-clock time
- the output `.mat` path

## Step 3: inspect the generated files

The command writes two files:

- `results/VortexArray2d_128.mat`
- `results/VortexArray2d_128_field.npz`

The `.mat` file stores NS2dLab-style timeseries arrays such as:

- `Ekin`
- `Diss`
- `Time`
- `ElapsedTime`

The `.npz` file stores the full final velocity field and grid spacing for downstream workflows.

## Step 4: compare outputs later if needed

If you produce two runs and want to compare their timeseries output, use:

```bash
nslab2d compare-reference --reference results/run_a.mat --candidate results/run_b.mat
```

## What you learned

You have now completed the smallest end-to-end NS2dLab workflow:

- run the solver
- save timeseries output
- save a reusable field snapshot

## Next steps

- [Compare CPU and GPU on the same case](compare-cpu-and-gpu.md)
- [Generate a flame/HIT workflow example](flame-hit-workflow.md)
- [Read the CLI reference](../reference/cli-reference.md)
