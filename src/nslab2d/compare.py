"""Cross-backend comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .config import NS2dConfig
from .solver import NS2dLabSolver, run_simulation


@dataclass(slots=True)
class BackendComparison:
    """Summary metrics for a CPU vs GPU comparison run."""

    config: NS2dConfig
    cpu_elapsed_time_seconds: float
    gpu_elapsed_time_seconds: float
    metrics: dict[str, float]


@dataclass(slots=True)
class BenchmarkEntry:
    """Timing result for one backend at one grid size."""

    backend: str
    N: int
    dt: float
    simutime_seconds: float
    nu: float
    elapsed_time_seconds: float


def _tg_exact(x: np.ndarray, y: np.ndarray, t: float, nu: float) -> tuple[np.ndarray, np.ndarray]:
    decay = np.exp(-nu * t)
    u = np.sin(x) * np.cos(y) * decay
    v = -np.cos(x) * np.sin(y) * decay
    return u, v


def _array_metrics(name: str, a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    """Return robust error metrics for two arrays.

    Relative metrics are scaled with the global infinity norm of the reference array
    instead of elementwise division. This avoids misleading blow-ups at points where
    the reference solution is exactly or nearly zero.
    """
    a = np.asarray(a, dtype=np.float64).reshape(-1)
    b = np.asarray(b, dtype=np.float64).reshape(-1)
    common = min(a.size, b.size)
    a = a[:common]
    b = b[:common]
    diff = b - a
    ref_scale = max(float(np.max(np.abs(a))), 1e-16)
    rmse = float(np.sqrt(np.mean(diff**2)))
    max_abs = float(np.max(np.abs(diff)))
    return {
        f"{name}_max_abs": max_abs,
        f"{name}_max_rel": max_abs / ref_scale,
        f"{name}_rmse": rmse,
        f"{name}_rmse_rel": rmse / ref_scale,
    }


def _run_with_initializer(config: NS2dConfig, initializer: Callable[[NS2dLabSolver], None] | None = None):
    """Run a simulation, optionally overwriting the initialized velocity field first."""
    solver = NS2dLabSolver(config)
    if initializer is not None:
        initializer(solver)
    return solver.run()


def compare_cpu_gpu(config: NS2dConfig, initializer: Callable[[NS2dLabSolver], None] | None = None) -> BackendComparison:
    """Run the same case on CPU and GPU and compare timeseries/final fields."""
    cpu_cfg = NS2dConfig(
        N=config.N,
        dt=config.dt,
        simutime_seconds=config.simutime_seconds,
        nu=config.nu,
        L=config.L,
        visualize=config.visualize,
        backend="cpu",
        fftw_threads=config.fftw_threads,
        fftw_cache_enable=config.fftw_cache_enable,
    )
    gpu_cfg = NS2dConfig(
        N=config.N,
        dt=config.dt,
        simutime_seconds=config.simutime_seconds,
        nu=config.nu,
        L=config.L,
        visualize=config.visualize,
        backend="gpu",
        fftw_threads=config.fftw_threads,
        fftw_cache_enable=config.fftw_cache_enable,
    )

    cpu_result = _run_with_initializer(cpu_cfg, initializer)
    gpu_result = _run_with_initializer(gpu_cfg, initializer)

    cpu_backend = cpu_result.backend
    gpu_backend = gpu_result.backend

    cpu_Ekin = cpu_backend.to_numpy(cpu_result.timeseries.Ekin)
    cpu_Diss = cpu_backend.to_numpy(cpu_result.timeseries.Diss)
    cpu_U = cpu_backend.to_numpy(cpu_result.fields.U)
    cpu_V = cpu_backend.to_numpy(cpu_result.fields.V)

    gpu_Ekin = gpu_backend.to_numpy(gpu_result.timeseries.Ekin)
    gpu_Diss = gpu_backend.to_numpy(gpu_result.timeseries.Diss)
    gpu_U = gpu_backend.to_numpy(gpu_result.fields.U)
    gpu_V = gpu_backend.to_numpy(gpu_result.fields.V)

    metrics: dict[str, float] = {}
    metrics.update(_array_metrics("Ekin", cpu_Ekin, gpu_Ekin))
    metrics.update(_array_metrics("Diss", cpu_Diss, gpu_Diss))
    metrics.update(_array_metrics("U_final", cpu_U, gpu_U))
    metrics.update(_array_metrics("V_final", cpu_V, gpu_V))

    return BackendComparison(
        config=config,
        cpu_elapsed_time_seconds=cpu_result.timeseries.ElapsedTime,
        gpu_elapsed_time_seconds=gpu_result.timeseries.ElapsedTime,
        metrics=metrics,
    )


def make_taylor_green_initializer(final_time_unused: float = 0.0) -> Callable[[NS2dLabSolver], None]:
    """Return an initializer that sets the exact Taylor–Green field at t=0."""

    def _initializer(solver: NS2dLabSolver) -> None:
        x = solver.backend.to_numpy(solver.fields.X)
        y = solver.backend.to_numpy(solver.fields.Y)
        u0, v0 = _tg_exact(x, y, 0.0, solver.config.nu)
        solver.fields.U = solver.backend.asarray(u0, dtype=solver.backend.xp.float64)
        solver.fields.V = solver.backend.asarray(v0, dtype=solver.backend.xp.float64)

    return _initializer


def benchmark_backend(backend: str, N_values: list[int], dt_values: list[float], simutime_seconds: float, nu: float, fftw_threads: int | None = None) -> list[BenchmarkEntry]:
    """Run a backend benchmark across multiple grid sizes."""
    if len(N_values) != len(dt_values):
        raise ValueError("N_values and dt_values must have the same length")
    results: list[BenchmarkEntry] = []
    for N, dt in zip(N_values, dt_values, strict=True):
        cfg = NS2dConfig(
            N=N,
            dt=dt,
            simutime_seconds=simutime_seconds,
            nu=nu,
            backend=backend,
            fftw_threads=fftw_threads,
        )
        result = run_simulation(cfg)
        results.append(
            BenchmarkEntry(
                backend=backend,
                N=N,
                dt=dt,
                simutime_seconds=simutime_seconds,
                nu=nu,
                elapsed_time_seconds=result.timeseries.ElapsedTime,
            )
        )
    return results


def validate_manuscript_cases() -> dict[str, object]:
    """Run CPU↔GPU comparison for the manuscript-scale validation cases."""
    cases = {
        "taylor_green": compare_cpu_gpu(
            NS2dConfig(N=32, dt=0.1, simutime_seconds=1.0, nu=1e-4),
            initializer=make_taylor_green_initializer(),
        ),
        "default_vortex_array": compare_cpu_gpu(
            NS2dConfig(N=128, dt=0.1, simutime_seconds=50.0, nu=1e-4),
        ),
        "pseudo_turbulence_256": compare_cpu_gpu(
            NS2dConfig(N=256, dt=0.05, simutime_seconds=50.0, nu=1e-4),
        ),
    }
    return {
        name: {
            "config": {
                "N": comp.config.N,
                "dt": comp.config.dt,
                "simutime_seconds": comp.config.simutime_seconds,
                "nu": comp.config.nu,
            },
            "cpu_elapsed_time_seconds": comp.cpu_elapsed_time_seconds,
            "gpu_elapsed_time_seconds": comp.gpu_elapsed_time_seconds,
            "metrics": comp.metrics,
        }
        for name, comp in cases.items()
    }
