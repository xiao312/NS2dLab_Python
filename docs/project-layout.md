# Project layout

This page explains where the important pieces of the repository live and what each part
is responsible for.

## Top-level structure

- `src/nslab2d/` — installable Python package
- `tests/` — automated regression tests
- `scripts/` — validation and figure-generation scripts
- `docs/` — documentation source used by MkDocs Material
- `.github/workflows/` — CI / deployment workflows

## Main package modules

### Core solver path

- `config.py` — immutable runtime configuration
- `backend.py` — CPU/GPU backend abstraction
- `operators.py` — spectral operators and the skew-symmetric advection pieces
- `projection.py` — Fourier-space Helmholtz–Hodge projection
- `diagnostics.py` — kinetic-energy and dissipation diagnostics
- `solver.py` — shared time-integration driver
- `io.py` — MATLAB-style timeseries output
- `cli.py` — command-line interface

### Combustion / post-processing helpers

- `field_io.py` — save/load full velocity snapshots as `.npz`
- `hit_stats.py` — 2D HIT statistics from a velocity field
- `flame_properties.py` — Cantera-based laminar flame properties
- `regime_diagram.py` — regime-point calculations and plotting
- `openfoam.py` — OpenFOAM 7 `U`-field export

## Tests

The test suite is intentionally split into fast, local/CI-friendly checks:

- numerical sanity checks
- I/O format checks
- backend agreement helpers
- optional Cantera smoke tests
- OpenFOAM export checks

Run all tests with:

```bash
pytest -q
```

## Validation scripts

The `scripts/` directory contains heavier or more visual checks that are useful for
release validation and manuscript-style reproduction:

- `render_default_ns2dlab_curl.py`
- `render_tg_vortex_validation.py`
- `render_2d_turbulence_validation.py`

These scripts write generated artifacts to `artifacts/`, which is intentionally ignored by git.
