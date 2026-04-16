# Overview

`NS2dLab_Python` is a fidelity-first Python port of the `NS2dLab` solver from the DNSLab MATLAB package.
It preserves the numerical structure of the original 2D pseudo-spectral solver while adding:

- a fast CPU backend with NumPy + PyFFTW
- an optional NVIDIA GPU backend with CuPy
- automated validation and backend-comparison workflows
- flame/HIT post-processing helpers
- OpenFOAM velocity-field export

## What you can do with the package

You can use the project to:

- run decaying 2D incompressible turbulence simulations on a periodic square domain
- compare CPU and GPU results using the same numerical algorithm
- validate the solver with analytical, physical, and manuscript-style checks
- save full velocity snapshots for downstream workflows
- compute HIT statistics and laminar flame properties
- place a case on a Borghi/Peters-style regime diagram
- export a final velocity field to an OpenFOAM 7 `U` file

## Original DNSLab reference

This repository is an independent Python port of the published DNSLab `NS2dLab` logic.

- Paper DOI: <https://doi.org/10.1016/j.cpc.2016.02.023>
- Dataset: <https://data.mendeley.com/datasets/6gtnjwwg8j/1>

## Recommended reading path

If you are new to the project, read the docs in this order:

1. [Install the package](installation.md)
2. [Run your first simulation](../tutorials/run-your-first-simulation.md)
3. [Use the CLI](../reference/cli-reference.md)
4. [Understand the solver design](../explanation/solver-algorithms.md)
5. [Review validation results](../results/validation-results.md)
