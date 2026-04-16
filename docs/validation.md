# Validation strategy

This document explains how the Python port is validated without relying on an interactive MATLAB step-by-step comparison or bundled MATLAB source files.

## Validation hierarchy

### 1. Source-faithful implementation

The first level of validation is direct fidelity to the MATLAB source:

- same wave-number generation
- same anti-aliasing mask
- same RK4 stage order
- same projection formula
- same diagnostics formulas

### 2. Analytical validation

The Taylor–Green vortex is used as an analytical benchmark.

Expected properties:

- divergence remains close to machine precision
- numerical solution matches the analytical decaying vortex closely on a coarse grid

The script:

- `scripts/render_tg_vortex_validation.py`

produces:

- velocity-vector visualization
- numerical vs analytical profile plot
- summary of divergence and error norms

### 3. Physical consistency checks

For turbulence-like runs, the code is checked against the periodic-domain energy identity:

`dEkin/dt = -χ`

Numerically, we compare:

- `-dEkin/dt`
- `χ(t)`

and evaluate the residual:

`R = |dEkin/dt + χ|`

The script:

- `scripts/render_2d_turbulence_validation.py`

uses 6th-order central differencing in time for `dEkin/dt` and reports residual statistics.

### 4. Qualitative manuscript checks

The default vortex-array setup is post-processed into curl / vorticity images for visual inspection against the manuscript-style NS2dLab figures.

The script:

- `scripts/render_default_ns2dlab_curl.py`

produces representative curl snapshots.

### 5. CPU/GPU agreement

The CPU backend is treated as the reference backend.
The GPU backend should reproduce the same run closely when using the same precision and configuration.

## Automated tests

The `tests/` directory contains fast tests intended for CI and local development.
They are deliberately smaller and cheaper than the manuscript-sized validation runs.

Currently covered:

- shape and dtype checks
- divergence-free initial projection
- short-run stability
- `.mat` output schema
- Taylor–Green vortex accuracy check
- conditional GPU backend tests that auto-skip if CUDA/CuPy is unavailable

## Manuscript-scale CPU↔GPU validation

The CLI command

```bash
nslab2d validate-manuscript-cases
```

runs CPU↔GPU comparisons for:

- Taylor–Green vortex
- default vortex-array case
- `256^2` pseudo-turbulence case

This is heavier than the automated test suite and is intended as a release/pre-push
validation step rather than a quick unit test.

## Why this project does not depend on bundled MATLAB reference files

This repository intentionally does not bundle the original MATLAB source tree or MATLAB-generated `.mat` reference files.
That means correctness must be established by a combination of:

- source-faithful algorithm design
- analytical cases
- physical consistency checks
- manuscript-style qualitative reproduction
- CPU/GPU backend agreement

This multi-layer approach is more robust than a single-file golden test and fits the current repository scope.
