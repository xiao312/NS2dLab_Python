from __future__ import annotations

import numpy as np

from nslab2d.config import NS2dConfig
from nslab2d.diagnostics import divergence
from nslab2d.solver import NS2dLabSolver


def test_short_run_produces_finite_timeseries():
    cfg = NS2dConfig(N=32, dt=0.1, simutime_seconds=0.5, fftw_threads=1)
    solver = NS2dLabSolver(cfg)
    result = solver.run()
    ekin = result.backend.to_numpy(result.timeseries.Ekin)
    diss = result.backend.to_numpy(result.timeseries.Diss)
    assert ekin.shape == (5,)
    assert diss.shape == (5,)
    assert np.all(np.isfinite(ekin))
    assert np.all(np.isfinite(diss))
    assert np.all(ekin > 0)
    assert np.all(diss >= 0)


def test_short_run_stays_divergence_free():
    cfg = NS2dConfig(N=32, dt=0.1, simutime_seconds=0.5, fftw_threads=1)
    solver = NS2dLabSolver(cfg)
    result = solver.run()
    div = divergence(result.fields.U, result.fields.V, result.fields.KX, result.fields.KY, result.backend)
    div_np = result.backend.to_numpy(div)
    assert float(np.max(np.abs(div_np))) < 1e-9
