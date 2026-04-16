# NS2dLab Python

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://xiao312.github.io/NS2dLab_Python/)
[![Docs workflow](https://github.com/xiao312/NS2dLab_Python/actions/workflows/docs.yml/badge.svg)](https://github.com/xiao312/NS2dLab_Python/actions/workflows/docs.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![GitHub repo size](https://img.shields.io/github/repo-size/xiao312/NS2dLab_Python)](https://github.com/xiao312/NS2dLab_Python)
[![GitHub last commit](https://img.shields.io/github/last-commit/xiao312/NS2dLab_Python)](https://github.com/xiao312/NS2dLab_Python/commits/main)

A Python port of the `NS2dLab` solver from the DNSLab MATLAB package.

Documentation site: <https://xiao312.github.io/NS2dLab_Python/>

Original DNSLab publication and dataset:

- Paper DOI: https://doi.org/10.1016/j.cpc.2016.02.023
- Dataset: https://data.mendeley.com/datasets/6gtnjwwg8j/1

This repository currently ports **only the 2D pseudo-spectral solver**. The 3D channel-flow solver is intentionally out of scope.

## Project goals

- preserve the MATLAB algorithm and numerical conventions as closely as practical
- provide a **fast CPU backend** via PyFFTW
- provide an **optional NVIDIA GPU backend** via CuPy
- keep outputs MATLAB-friendly for comparison and post-processing
- provide validation scripts for the main manuscript examples

## What is implemented

The Python package reproduces the NS2dLab workflow and adds downstream utilities for
flame-in-HIT studies:

- periodic square domain with side length `L = 2π`
- pseudo-spectral differentiation with `fft2` / `ifft2`
- skew-symmetric advection term
- explicit RK4 time stepping using the same stage order as the MATLAB code
- Helmholtz–Hodge projection in Fourier space
- timeseries diagnostics:
  - kinetic energy `Ekin`
  - dissipation rate `Diss`
  - simulation time `Time`
- saved velocity-field snapshots for downstream workflows
- 2D HIT statistics from the evolved field
- Cantera-based laminar flame speed / thickness calculations
- Borghi/Peters-style turbulent flame regime placement
- OpenFOAM 7 `U`-field export for structured 2D cases

## Repository layout

- `src/nslab2d/` - package source
- `tests/` - automated tests
- `scripts/` - validation / figure-generation scripts
- `docs/` - algorithm notes, backend spec, validation notes, and flame/HIT workflow notes
- no bundled MATLAB source; validation is based on analytical cases, manuscript-style checks, and CPU/GPU agreement

## Installation

### Using `uv`

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

Optional GPU dependencies:

```bash
uv pip install -e '.[gpu]'
```

The current tested pip-based GPU stack is:

- `cupy-cuda12x`
- `nvidia-cuda-nvrtc-cu12`
- `nvidia-cufft-cu12`
- `nvidia-nvjitlink-cu12`

These are included in the `gpu` extra.

Optional combustion dependencies (Cantera-based flame properties):

```bash
uv pip install -e '.[combustion]'
```

Development dependencies:

```bash
uv pip install -e '.[dev]'
```

Documentation-site dependencies:

```bash
uv pip install -e '.[docs]'
```

Everything used in the full workflow:

```bash
uv pip install -e '.[full]'
```

## Running the solver

### CPU

```bash
nslab2d run \
  --backend cpu \
  --N 128 \
  --dt 0.1 \
  --simutime-seconds 50 \
  --output results/VortexArray2d_128_py.mat
```

### GPU

```bash
nslab2d run \
  --backend gpu \
  --N 128 \
  --dt 0.1 \
  --simutime-seconds 50 \
  --output results/VortexArray2d_128_gpu.mat
```

### Save the final velocity field for downstream combustion/OpenFOAM workflows

```bash
nslab2d run \
  --backend cpu \
  --N 256 \
  --dt 0.05 \
  --simutime-seconds 50 \
  --output results/VortexArray2d_256.mat \
  --save-field-npz results/VortexArray2d_256_field.npz
```

## Comparing `.mat` outputs

```bash
nslab2d compare-reference \
  --reference results/run_a.mat \
  --candidate results/run_b.mat
```

This command compares the saved timeseries fields `Ekin`, `Diss`, and `Time` between any two NS2dLab-style `.mat` outputs.

## GPU tooling

Device information:

```bash
nslab2d device-info
```

CPU vs GPU comparison:

```bash
nslab2d compare-backends --N 64 --dt 0.1 --simutime-seconds 2
```

Backend benchmarking:

```bash
nslab2d benchmark --backend cpu --N 64,128,256 --dt 0.1,0.1,0.05 --simutime-seconds 5
nslab2d benchmark --backend gpu --N 64,128,256 --dt 0.1,0.1,0.05 --simutime-seconds 5
```

Manuscript-scale CPU↔GPU validation:

```bash
nslab2d validate-manuscript-cases --output results/manuscript_gpu_validation.json
```

## Flame/HIT workflow commands

Compute HIT statistics from a saved field:

```bash
nslab2d hit-stats --field-npz results/VortexArray2d_256_field.npz
```

Compute laminar flame properties with Cantera:

```bash
nslab2d flame-properties \
  --mechanism gri30.yaml \
  --fuel CH4 \
  --oxidizer 'O2:1.0, N2:3.76' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325
```

Place a case on a Borghi/Peters-style turbulent flame regime diagram:

```bash
nslab2d regime-diagram \
  --field-npz results/VortexArray2d_256_field.npz \
  --mechanism gri30.yaml \
  --fuel CH4 \
  --oxidizer 'O2:1.0, N2:3.76' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325 \
  --output artifacts/regime_diagram.png
```

Export a saved field to an OpenFOAM 7 `U` file:

```bash
nslab2d export-openfoam-u \
  --field-npz results/VortexArray2d_256_field.npz \
  --case-dir /path/to/openfoam_case \
  --time-dir 0 \
  --ordering x-fastest
```

## Validation scripts

The repository includes scripts used to reproduce the main qualitative / quantitative checks discussed while developing the port:

- `scripts/render_default_ns2dlab_curl.py`
  - default vortex-array case
  - renders curl / vorticity snapshots
- `scripts/render_tg_vortex_validation.py`
  - Taylor–Green vortex analytical validation
  - velocity vectors + profile comparison
- `scripts/render_2d_turbulence_validation.py`
  - 2D pseudo-turbulence example
  - energy identity check `-dEkin/dt ≈ χ(t)`

Generated files are written to `artifacts/` and intentionally ignored by git.

## Tests

Run all tests with:

```bash
pytest -q
```

Current tests cover:

- field construction and datatype/shape sanity
- divergence-free projected initialization
- short-run solver stability and finiteness
- MATLAB-friendly `.mat` output structure
- Taylor–Green validation accuracy against the analytical solution
- conditional GPU backend tests
- HIT statistics helpers
- OpenFOAM field export helpers
- Cantera flame-property smoke test
- regime-diagram helper calculations

## Documentation

This repository now includes a MkDocs Material site source.

Serve it locally:

```bash
uv pip install -e '.[docs]'
mkdocs serve
```

Build it locally:

```bash
mkdocs build --strict
```

Main pages:

- `docs/index.md` - site landing page
- `docs/getting-started.md` - installation and first-run workflow
- `docs/cli.md` - CLI-oriented usage guide
- `docs/project-layout.md` - repository/module structure
- `docs/NS2dLab_backend_spec.md` - backend design contract
- `docs/algorithms.md` - solver algorithm overview
- `docs/validation.md` - validation strategy and current checks
- `docs/gpu.md` - GPU backend notes and tooling
- `docs/flame_hit_workflow.md` - end-to-end flame-in-HIT workflow
- `docs/api.md` - API reference via `mkdocstrings`
- `CONTRIBUTING.md` - development workflow and contribution guidance

## Validation basis

This repository does not bundle the original MATLAB source or MATLAB-produced reference files.
Instead, validation is based on:

1. source-faithful algorithm design
2. analytical cases such as Taylor–Green vortex
3. manuscript-style qualitative and physical-consistency checks
4. CPU/GPU backend agreement

## Reference to original DNSLab

The original DNSLab work can be found at:

- Dataset: https://data.mendeley.com/datasets/6gtnjwwg8j/1
- DOI: https://doi.org/10.1016/j.cpc.2016.02.023

Suggested citation:

> Vuorinen, V., & Keskinen, K. DNSLab: A gateway to turbulent flow simulation in Matlab. Computer Physics Communications (2016). https://doi.org/10.1016/j.cpc.2016.02.023

## Provenance

This repository contains an independent Python port of the NS2dLab solver logic with manuscript-driven validation and backend cross-checking.
It is not an official distribution of the original DNSLab MATLAB package.

# NS2dLab_Python
