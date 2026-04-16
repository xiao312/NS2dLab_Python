from __future__ import annotations

import pytest

from nslab2d.backend import get_gpu_info, gpu_is_available, make_backend
from nslab2d.compare import compare_cpu_gpu
from nslab2d.config import NS2dConfig


pytestmark = pytest.mark.skipif(not gpu_is_available(), reason="CUDA/CuPy GPU backend unavailable")


def test_get_gpu_info_reports_visible_device():
    info = get_gpu_info()
    assert info["gpu_available"] if "gpu_available" in info else True
    assert info["device_count"] >= 1
    assert len(info["devices"]) >= 1


def test_gpu_backend_can_be_constructed():
    backend = make_backend("gpu")
    assert backend.name == "gpu"


def test_short_run_cpu_gpu_equivalence():
    cfg = NS2dConfig(N=32, dt=0.1, simutime_seconds=0.5, nu=1e-4, fftw_threads=1)
    comparison = compare_cpu_gpu(cfg)
    assert comparison.metrics["Ekin_max_rel"] < 1e-10
    assert comparison.metrics["Diss_max_rel"] < 1e-10
    assert comparison.metrics["U_final_rmse"] < 1e-12
    assert comparison.metrics["V_final_rmse"] < 1e-12
