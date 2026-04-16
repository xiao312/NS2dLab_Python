# NS2dLab Python

`NS2dLab_Python` is a Python port of the `NS2dLab` solver from the DNSLab MATLAB package.
It focuses on **fidelity first**: the numerical structure of the original MATLAB algorithm
is preserved as closely as practical while adding a clean Python package, optional GPU
execution, automated tests, and workflow utilities for downstream combustion studies.

## What this project provides

- a 2D incompressible pseudo-spectral Navier–Stokes solver on a periodic square domain
- a fast CPU backend using NumPy + PyFFTW
- an optional NVIDIA GPU backend using CuPy
- MATLAB-friendly `.mat` output for timeseries diagnostics
- validation tools based on analytical checks, physical consistency, and CPU↔GPU agreement
- utilities for flame-in-HIT studies:
  - save full velocity-field snapshots
  - compute 2D HIT statistics
  - compute laminar flame properties with Cantera
  - place a case on a Borghi/Peters-style regime diagram
  - export a velocity field to an OpenFOAM 7 `U` file

## Design philosophy

This repository is organized around three ideas:

1. **Source-faithful solver implementation**  
   The CPU reference path keeps the original MATLAB semantics wherever possible.
2. **One solver, multiple backends**  
   CPU and GPU execution share the same solver logic, differing only in array/FFT backend code.
3. **Practical reproducibility**  
   The repository includes documentation, CLI commands, tests, and validation scripts so users can
   understand both *what* the package does and *how* the calculations are carried out.

## Quick example

Run a short CPU simulation:

```bash
nslab2d run \
  --backend cpu \
  --N 128 \
  --dt 0.1 \
  --simutime-seconds 10 \
  --output results/VortexArray2d_128.mat
```

Save a final field snapshot for downstream analysis:

```bash
nslab2d run \
  --backend cpu \
  --N 256 \
  --dt 0.05 \
  --simutime-seconds 50 \
  --output results/VortexArray2d_256.mat \
  --save-field-npz results/VortexArray2d_256_field.npz
```

## Documentation map

If you are new to the project, the fastest path is:

1. [Getting Started](getting-started.md) — install the package and run the main commands
2. [CLI Guide](cli.md) — understand the available workflows
3. [Solver Algorithms](algorithms.md) — learn how the numerical method is implemented
4. [Validation Strategy](validation.md) — see how correctness is established
5. [Flame-in-HIT Workflow](flame_hit_workflow.md) — use the turbulence field in combustion studies
6. [API Reference](api.md) — inspect module-level API documentation

## Original DNSLab reference

This project is an independent Python port of the published DNSLab `NS2dLab` solver logic.

- Paper DOI: <https://doi.org/10.1016/j.cpc.2016.02.023>
- Dataset: <https://data.mendeley.com/datasets/6gtnjwwg8j/1>

Suggested citation:

> Vuorinen, V., & Keskinen, K. DNSLab: A gateway to turbulent flow simulation in Matlab.
> *Computer Physics Communications* (2016). <https://doi.org/10.1016/j.cpc.2016.02.023>
