from __future__ import annotations

import numpy as np

from nslab2d.backend import make_backend
from nslab2d.config import NS2dConfig
from nslab2d.diagnostics import divergence
from nslab2d.operators import create_fields


def test_create_fields_shapes_and_dtypes():
    backend = make_backend("cpu", fftw_threads=1)
    cfg = NS2dConfig(N=32, dt=0.1, simutime_seconds=0.2, fftw_threads=1)
    fields = create_fields(cfg, backend)
    assert fields.U.shape == (32, 32)
    assert fields.V.shape == (32, 32)
    assert fields.KX.shape == (32, 32)
    assert fields.AA.shape == (32, 32)
    assert fields.U.dtype == np.float64
    assert fields.V.dtype == np.float64
    assert fields.KX.dtype == np.float64
    assert fields.AA.dtype == np.float64


def test_initial_projection_is_divergence_free():
    backend = make_backend("cpu", fftw_threads=1)
    cfg = NS2dConfig(N=32, dt=0.1, simutime_seconds=0.2, fftw_threads=1)
    fields = create_fields(cfg, backend)
    div = divergence(fields.U, fields.V, fields.KX, fields.KY, backend)
    assert float(np.max(np.abs(div))) < 1e-10
