from __future__ import annotations

import numpy as np

from nslab2d.config import NS2dConfig
from nslab2d.diagnostics import divergence
from nslab2d.solver import NS2dLabSolver


def _tg_exact(x, y, t, nu):
    decay = np.exp(-nu * t)
    u = np.sin(x) * np.cos(y) * decay
    v = -np.cos(x) * np.sin(y) * decay
    return u, v


def test_taylor_green_validation_case_remains_accurate():
    """The coarse Taylor–Green benchmark should stay close to the exact solution."""
    final_time = 1.0
    cfg = NS2dConfig(N=32, dt=0.1, simutime_seconds=final_time, nu=1e-4, fftw_threads=1)
    solver = NS2dLabSolver(cfg)

    x = solver.backend.to_numpy(solver.fields.X)
    y = solver.backend.to_numpy(solver.fields.Y)
    u0, v0 = _tg_exact(x, y, 0.0, cfg.nu)
    solver.fields.U = solver.backend.asarray(u0, dtype=solver.backend.xp.float64)
    solver.fields.V = solver.backend.asarray(v0, dtype=solver.backend.xp.float64)

    result = solver.run()
    u_num = result.backend.to_numpy(result.fields.U)
    v_num = result.backend.to_numpy(result.fields.V)
    u_ex, v_ex = _tg_exact(x, y, final_time, cfg.nu)

    div = result.backend.to_numpy(
        divergence(result.fields.U, result.fields.V, result.fields.KX, result.fields.KY, result.backend)
    )
    assert float(np.max(np.abs(div))) < 1e-10
    assert float(np.max(np.abs(u_num - u_ex))) < 2e-4
    assert float(np.max(np.abs(v_num - v_ex))) < 2e-4
