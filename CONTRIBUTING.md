# Contributing

## Development setup

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
```

Optional GPU support:

```bash
uv pip install -e '.[gpu]'
```

## Running tests

```bash
pytest -q
```

## Coding guidelines

- prefer clarity over micro-optimizations in the reference implementation
- preserve MATLAB algorithm semantics unless there is a documented reason not to
- keep CPU and GPU code paths aligned through the shared backend abstraction
- add docstrings and short explanatory comments for non-obvious numerical steps
- avoid changing output field names unless compatibility is intentionally broken and documented

## Validation workflow

Before pushing meaningful solver changes:

1. run the automated test suite
2. run the Taylor–Green validation script if algorithmic changes affect correctness
3. run the turbulence energy-identity script if diagnostics or timestep logic changed
4. run `nslab2d validate-manuscript-cases` before major releases or GPU-related pushes
5. inspect generated figures if visualization/post-processing code changed

## What not to commit

The following are intentionally ignored by git:

- `.venv/`
- `artifacts/`
- generated `.mat`, `.npy`, `.png` files
- local caches

## Scope note

This repository currently targets the `NS2dLab` solver only.
Contributions should not introduce unrelated 3D solver work unless the project scope is explicitly expanded.
