# GPU backend

This project provides an optional NVIDIA GPU backend for NS2dLab using CuPy.

## Design goals

- keep the numerical algorithm identical to the CPU reference path
- keep all timestep arrays on the GPU during the run
- use double precision (`float64` / `complex128`) for consistency with the CPU backend
- make CPU↔GPU comparison easy through CLI tooling

## Backend summary

- CPU backend: NumPy + PyFFTW
- GPU backend: CuPy + CuPy FFT

The solver implementation itself is shared. Only array allocation, FFT evaluation,
and host/device data transfer are backend-specific.

## Installation

Install the base package first:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

Then install the tested pip-based GPU stack:

```bash
uv pip install -e '.[gpu]'
```

This currently installs:

- `cupy-cuda12x`
- `nvidia-cuda-nvrtc-cu12`
- `nvidia-cufft-cu12`
- `nvidia-nvjitlink-cu12`

The extra packages are included because some pip/venv environments expose the GPU
(driver tools like `nvidia-smi` work) but do not provide NVRTC / cuFFT shared
libraries on the default linker path. The backend now preloads those wheel-provided
libraries automatically.

If your system needs a different CuPy wheel, install the appropriate `cupy-cudaXX`
variant manually and make sure matching NVIDIA runtime wheels are available.

## Device info

Check that CuPy can see the device:

```bash
nslab2d device-info
```

This prints:

- whether GPU execution is available
- CuPy version
- CUDA runtime / driver versions
- visible devices and basic properties

## CPU vs GPU comparison

Run the same case on CPU and GPU and compare timeseries/final fields:

```bash
nslab2d compare-backends --N 64 --dt 0.1 --simutime-seconds 2
```

## Benchmarking

Benchmark a single backend over several grid sizes:

```bash
nslab2d benchmark --backend cpu --N 64,128,256 --dt 0.1,0.1,0.05 --simutime-seconds 5
nslab2d benchmark --backend gpu --N 64,128,256 --dt 0.1,0.1,0.05 --simutime-seconds 5
```

`--N` and `--dt` are comma-separated lists and must have the same length.

## Manuscript-scale backend validation

Run the three main CPU↔GPU comparison cases used in this project:

```bash
nslab2d validate-manuscript-cases --output results/manuscript_gpu_validation.json
```

This validates:

- Taylor–Green vortex
- default vortex-array case
- `256^2` pseudo-turbulence case

Reported metrics include:

- `Ekin` max abs / max rel / RMSE
- `Diss` max abs / max rel / RMSE
- final `U` and `V` field differences
- elapsed time for each backend

## Notes

- small cases may not be faster on GPU because of launch/setup overhead
- the CPU backend remains the reference backend for correctness
- exact bitwise identity between CPU and GPU is not required; close agreement is
  the target
