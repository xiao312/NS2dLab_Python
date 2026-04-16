# Install GPU support

Use this guide when you already understand the package basics and want to enable the optional GPU backend.

## Install the GPU extra

```bash
uv pip install -e '.[gpu]'
```

This installs the currently tested pip-based GPU stack:

- `cupy-cuda12x`
- `nvidia-cuda-nvrtc-cu12`
- `nvidia-cufft-cu12`
- `nvidia-nvjitlink-cu12`

## Verify that the GPU is available

```bash
nslab2d device-info
```

## Run a small backend comparison

```bash
nslab2d compare-backends --N 64 --dt 0.1 --simutime-seconds 2
```

## Troubleshooting

If `nslab2d device-info` does not report a usable GPU, check:

- that the NVIDIA driver is installed and visible to `nvidia-smi`
- that the CuPy wheel matches your CUDA/driver environment
- that the environment contains the expected NVIDIA runtime wheels

For design details, see [GPU backend](../explanation/gpu-backend.md).
