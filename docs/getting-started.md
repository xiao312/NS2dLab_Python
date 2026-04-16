# Getting started

This page explains the package layout, installation options, and the smallest set of
commands a new user needs to become productive quickly.

## Repository scope

This repository currently ports **only the 2D `NS2dLab` solver** from DNSLab.
The 3D `Channel3dLab` solver is intentionally out of scope.

## Installation

### Base package

Using `uv`:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

This installs the CPU solver path and the dependencies needed for the documented
validation scripts.

### Optional GPU support

```bash
uv pip install -e '.[gpu]'
```

The tested pip-based GPU stack currently includes:

- `cupy-cuda12x`
- `nvidia-cuda-nvrtc-cu12`
- `nvidia-cufft-cu12`
- `nvidia-nvjitlink-cu12`

### Optional combustion support

```bash
uv pip install -e '.[combustion]'
```

This installs Cantera so the package can compute laminar flame speed and thickness for
regime-diagram placement.

### Full developer/docs environment

```bash
uv pip install -e '.[full]'
uv pip install -e '.[docs]'
```

## First solver run

Run a short CPU simulation:

```bash
nslab2d run \
  --backend cpu \
  --N 128 \
  --dt 0.1 \
  --simutime-seconds 10 \
  --output results/VortexArray2d_128.mat
```

This creates a MATLAB-friendly `.mat` file containing the main timeseries arrays:

- `Ekin`
- `Diss`
- `Time`
- `ElapsedTime`

## Save a field for downstream workflows

If you need the fully evolved velocity field for analysis, combustion initialization,
or OpenFOAM export, add:

```bash
--save-field-npz results/VortexArray2d_128_field.npz
```

Example:

```bash
nslab2d run \
  --backend cpu \
  --N 256 \
  --dt 0.05 \
  --simutime-seconds 50 \
  --output results/VortexArray2d_256.mat \
  --save-field-npz results/VortexArray2d_256_field.npz
```

## Useful next commands

Compare two `.mat` outputs:

```bash
nslab2d compare-reference --reference results/run_a.mat --candidate results/run_b.mat
```

Inspect GPU availability:

```bash
nslab2d device-info
```

Compare CPU and GPU on the same case:

```bash
nslab2d compare-backends --N 64 --dt 0.1 --simutime-seconds 2
```

## How the package is organized

- `src/nslab2d/` — package source code
- `tests/` — automated tests
- `scripts/` — validation / figure-generation scripts
- `docs/` — documentation source for this site

For a narrative explanation of the solver logic, continue to [Solver Algorithms](algorithms.md).
