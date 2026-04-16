# Project layout

## Top-level structure

- `src/nslab2d/` — installable Python package
- `tests/` — automated regression tests
- `scripts/` — validation and figure-generation scripts
- `docs/` — documentation source used by MkDocs Material
- `.github/workflows/` — CI and deployment workflows

## Main package modules

### Core solver path

- `config.py`
- `backend.py`
- `operators.py`
- `projection.py`
- `diagnostics.py`
- `solver.py`
- `io.py`
- `cli.py`

### Combustion and post-processing helpers

- `field_io.py`
- `hit_stats.py`
- `flame_properties.py`
- `regime_diagram.py`
- `openfoam.py`

## Related pages

- [CLI reference](cli-reference.md)
- [API reference](api-reference.md)
- [Solver algorithms](../explanation/solver-algorithms.md)
