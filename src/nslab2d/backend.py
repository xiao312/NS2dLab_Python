"""Backend abstraction for array and FFT operations.

The solver code is written once against this minimal interface. The CPU backend
uses NumPy + PyFFTW, while the optional GPU backend uses CuPy.
"""

from __future__ import annotations

import ctypes
import os
import site
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(slots=True)
class Backend:
    name: str
    xp: Any

    def asarray(self, obj: Any, dtype: Any | None = None) -> Any:
        raise NotImplementedError

    def zeros(self, shape: tuple[int, ...], dtype: Any) -> Any:
        return self.xp.zeros(shape, dtype=dtype)

    def fft2(self, arr: Any) -> Any:
        raise NotImplementedError

    def ifft2(self, arr: Any) -> Any:
        raise NotImplementedError

    def real(self, arr: Any) -> Any:
        return self.xp.real(arr)

    def to_numpy(self, arr: Any) -> np.ndarray:
        raise NotImplementedError

    def synchronize(self) -> None:
        return None


class CPUBackend(Backend):
    """Reference backend based on NumPy arrays and PyFFTW FFTs.

    This is the default backend used for correctness checks and automated tests.
    PyFFTW's NumPy-compatible interface is used here because NS2dLab repeatedly
    evaluates FFTs with fixed shapes and benefits from FFTW planning/caching.
    """

    def __init__(self, threads: int | None = None, enable_cache: bool = True) -> None:
        import pyfftw
        from pyfftw.interfaces import cache, numpy_fft

        super().__init__(name="cpu", xp=np)
        self._numpy_fft = numpy_fft
        self._pyfftw = pyfftw
        if threads is None:
            threads = max(1, (os.cpu_count() or 1))
        # Set FFTW's global thread count once for this backend instance.
        pyfftw.config.NUM_THREADS = threads
        self.threads = threads
        if enable_cache:
            cache.enable()
        self._cache_enabled = enable_cache

    def asarray(self, obj: Any, dtype: Any | None = None) -> np.ndarray:
        return np.asarray(obj, dtype=dtype)

    def fft2(self, arr: np.ndarray) -> np.ndarray:
        return self._numpy_fft.fft2(arr)

    def ifft2(self, arr: np.ndarray) -> np.ndarray:
        return self._numpy_fft.ifft2(arr)

    def to_numpy(self, arr: Any) -> np.ndarray:
        return np.asarray(arr)


class GPUBackend(Backend):
    """Optional backend based on CuPy arrays and CuPy FFTs.

    Import is deliberately lazy so CPU-only environments can still install and run
    the package without a CUDA stack.
    """

    def __init__(self) -> None:
        cp = import_cupy()
        super().__init__(name="gpu", xp=cp)
        self.cp = cp

    def asarray(self, obj: Any, dtype: Any | None = None) -> Any:
        return self.cp.asarray(obj, dtype=dtype)

    def fft2(self, arr: Any) -> Any:
        return self.cp.fft.fft2(arr)

    def ifft2(self, arr: Any) -> Any:
        return self.cp.fft.ifft2(arr)

    def to_numpy(self, arr: Any) -> np.ndarray:
        return self.cp.asnumpy(arr)

    def synchronize(self) -> None:  # pragma: no cover - environment dependent
        # Device-wide synchronization is appropriate here because NS2dLab currently
        # uses the default stream and we only need synchronization for timing and
        # result extraction boundaries.
        self.cp.cuda.Device().synchronize()


def _candidate_cuda_lib_dirs() -> list[Path]:
    """Return likely library directories for pip-installed NVIDIA CUDA wheels."""
    candidates: list[Path] = []
    for root in site.getsitepackages():
        base = Path(root) / "nvidia"
        for rel in [
            Path("cuda_nvrtc/lib"),
            Path("cuda_runtime/lib"),
            Path("cublas/lib"),
            Path("cufft/lib"),
            Path("curand/lib"),
            Path("cusolver/lib"),
            Path("cusparse/lib"),
            Path("nvjitlink/lib"),
        ]:
            path = base / rel
            if path.exists():
                candidates.append(path)
    return candidates


def _preload_cuda_runtime_libs() -> None:
    """Preload CUDA shared libraries for CuPy in pip/venv environments.

    Some environments expose the GPU driver (`nvidia-smi` works) but do not have a
    system CUDA toolkit on the default linker path.  In that case CuPy can fail when
    looking for `libnvrtc.so`.  We proactively load any pip-installed NVIDIA shared
    libraries with `RTLD_GLOBAL` so CuPy/NVRTC can resolve them.
    """
    for directory in _candidate_cuda_lib_dirs():
        for pattern in (
            "libnvrtc.so*",
            "libcudart.so*",
            "libcufft.so*",
            "libcurand.so*",
            "libcusolver.so*",
            "libcusparse.so*",
            "libnvJitLink.so*",
        ):
            for libpath in sorted(directory.glob(pattern)):
                try:
                    ctypes.CDLL(str(libpath), mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    pass


def import_cupy():
    """Import CuPy with a consistent, user-facing error message."""
    try:
        _preload_cuda_runtime_libs()
        import cupy as cp
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "GPU backend requested but CuPy is not available or failed to initialize. "
            "Install a matching CuPy package for your CUDA runtime, e.g. `cupy-cuda12x`, "
            "and ensure NVRTC/CUDA shared libraries are visible."
        ) from exc
    return cp


def gpu_is_available() -> bool:
    """Return whether CuPy can be imported and sees at least one CUDA device."""
    try:
        cp = import_cupy()
        return cp.cuda.runtime.getDeviceCount() > 0
    except Exception:  # pragma: no cover - environment dependent
        return False


def get_gpu_info() -> dict[str, object]:
    """Return basic device/runtime information for the active CUDA environment."""
    cp = import_cupy()
    device_count = int(cp.cuda.runtime.getDeviceCount())
    devices: list[dict[str, object]] = []
    for idx in range(device_count):
        props = cp.cuda.runtime.getDeviceProperties(idx)
        with cp.cuda.Device(idx):
            free_bytes, total_bytes = cp.cuda.runtime.memGetInfo()
        devices.append(
            {
                "id": idx,
                "name": props["name"].decode() if isinstance(props["name"], bytes) else props["name"],
                "total_global_mem_bytes": int(props["totalGlobalMem"]),
                "multiprocessor_count": int(props["multiProcessorCount"]),
                "compute_capability": f"{props['major']}.{props['minor']}",
                "current_free_mem_bytes": int(free_bytes),
                "current_total_mem_bytes": int(total_bytes),
            }
        )
    runtime_version = cp.cuda.runtime.runtimeGetVersion()
    driver_version = cp.cuda.runtime.driverGetVersion()
    return {
        "cupy_version": cp.__version__,
        "cuda_runtime_version": int(runtime_version),
        "cuda_driver_version": int(driver_version),
        "device_count": device_count,
        "devices": devices,
    }


def make_backend(name: str, *, fftw_threads: int | None = None, fftw_cache_enable: bool = True) -> Backend:
    """Construct the requested backend by name."""
    normalized = name.lower()
    if normalized == "cpu":
        return CPUBackend(threads=fftw_threads, enable_cache=fftw_cache_enable)
    if normalized == "gpu":
        return GPUBackend()
    raise ValueError(f"Unknown backend: {name}")
