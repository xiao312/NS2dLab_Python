# Installation

This page explains how to install the package for CPU use, GPU use, and the full documentation/development workflow.

## Scope

This repository ports **only the 2D `NS2dLab` solver** from DNSLab.
The 3D `Channel3dLab` solver is intentionally out of scope.

## Install the base package

Using `uv`:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

This installs the CPU solver path and the dependencies needed for the base package.

## Install optional GPU support

```bash
uv pip install -e '.[gpu]'
```

The tested pip-based GPU stack currently includes:

- `cupy-cuda12x`
- `nvidia-cuda-nvrtc-cu12`
- `nvidia-cufft-cu12`
- `nvidia-nvjitlink-cu12`

## Install optional combustion support

```bash
uv pip install -e '.[combustion]'
```

This installs Cantera so the package can compute laminar flame speed and flame thickness.

## Install documentation and development dependencies

```bash
uv pip install -e '.[dev]'
uv pip install -e '.[docs]'
```

Or install everything used in the current repo workflows:

```bash
uv pip install -e '.[full]'
```

## Verify the installation

Run the test suite:

```bash
pytest -q
```

Inspect GPU availability if you installed GPU support:

```bash
nslab2d device-info
```

## Next step

Continue to [Run your first simulation](../tutorials/run-your-first-simulation.md).
