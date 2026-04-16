# NS2dLab Python

A Python port of the `NS2dLab` solver from the DNSLab MATLAB package.

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

The Python package reproduces the NS2dLab workflow:

- periodic square domain with side length `L = 2π`
- pseudo-spectral differentiation with `fft2` / `ifft2`
- skew-symmetric advection term
- explicit RK4 time stepping using the same stage order as the MATLAB code
- Helmholtz–Hodge projection in Fourier space
- timeseries diagnostics:
  - kinetic energy `Ekin`
  - dissipation rate `Diss`
  - simulation time `Time`

## Repository layout

- `src/nslab2d/` - package source
- `tests/` - automated tests
- `scripts/` - validation / figure-generation scripts
- `docs/` - algorithm notes, backend spec, validation notes
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

Development dependencies:

```bash
uv pip install -e '.[dev]'
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

## Documentation

- `docs/NS2dLab_backend_spec.md` - backend design contract
- `docs/algorithms.md` - solver algorithm overview
- `docs/validation.md` - validation strategy and current checks
- `docs/gpu.md` - GPU backend notes and tooling
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
