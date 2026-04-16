"""High-level solver driver for NS2dLab."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .backend import Backend, make_backend
from .config import NS2dConfig
from .diagnostics import gather_timeseries
from .operators import compute_advection_skew, compute_diffusion, create_fields
from .projection import project
from .types import NS2dFields, NS2dTimeseries


@dataclass(slots=True)
class RunResult:
    """Container returned after a completed simulation run."""
    config: NS2dConfig
    fields: NS2dFields
    timeseries: NS2dTimeseries
    backend: Backend


class NS2dLabSolver:
    """Stateful solver object for the NS2dLab timestep loop.

    The solver owns the mutable field arrays and diagnostic timeseries.  The public
    workflow is:

    1. create the solver
    2. optionally modify the initialized fields
    3. call `step()` manually or `run()` for the full simulation
    """

    def __init__(self, config: NS2dConfig, backend: Backend | None = None) -> None:
        self.config = config
        self.backend = backend or make_backend(
            config.backend,
            fftw_threads=config.fftw_threads,
            fftw_cache_enable=config.fftw_cache_enable,
        )
        self.fields = create_fields(config, self.backend)
        xp = self.backend.xp
        self.timeseries = NS2dTimeseries(
            Ekin=xp.zeros(config.simutime_steps, dtype=xp.float64),
            Diss=xp.zeros(config.simutime_steps, dtype=xp.float64),
            Time=self.backend.asarray(
                xp.linspace(0.0, config.simutime_seconds, config.simutime_steps),
                dtype=xp.float64,
            ),
            ElapsedTime=0.0,
        )

    def step(self) -> None:
        """Advance the solution by one physical timestep.

        This method follows the logic of `SolveNavierStokes2D.m` closely.  The
        stage arrays are intentionally kept in a MATLAB-like style to make the port
        easy to audit term-by-term.
        """
        cfg = self.config
        f = self.fields
        Uold = f.U
        Vold = f.V
        U = f.U
        V = f.V
        Uc = f.U
        Vc = f.V

        for rk in range(4):
            # Each stage computes advection + diffusion, projects the increment,
            # and then updates the intermediate RK state using the original `a` and
            # `b` coefficient vectors.
            dUconv, dVconv = compute_advection_skew(U, V, f.KX, f.KY, f.AA, cfg.dt, self.backend)
            dUdiff, dVdiff = compute_diffusion(U, V, f.KX, f.KY, cfg.nu, cfg.dt, self.backend)
            dU = dUconv + dUdiff
            dV = dVconv + dVdiff
            dU, dV = project(dU, dV, f.KX, f.KY, f.AA, self.backend)

            if rk < 4 - 1:
                U = Uold + f.b[rk] * dU
                V = Vold + f.b[rk] * dV
            Uc = Uc + f.a[rk] * dU
            Vc = Vc + f.a[rk] * dV

        f.U = Uc
        f.V = Vc
        f.U, f.V = project(f.U, f.V, f.KX, f.KY, f.AA, self.backend)

    def run(self) -> RunResult:
        """Run the complete simulation and fill the diagnostic timeseries."""
        start = time.perf_counter()
        for t in range(self.config.simutime_steps):
            self.step()
            ekin, diss = gather_timeseries(
                self.fields.U,
                self.fields.V,
                self.fields.KX,
                self.fields.KY,
                self.fields.dx,
                self.config.L,
                self.config.nu,
                self.backend,
            )
            self.timeseries.Ekin[t] = ekin
            self.timeseries.Diss[t] = diss
        self.backend.synchronize()
        self.timeseries.ElapsedTime = time.perf_counter() - start
        return RunResult(self.config, self.fields, self.timeseries, self.backend)


def run_simulation(config: NS2dConfig) -> RunResult:
    """Convenience wrapper for one-shot simulations."""
    return NS2dLabSolver(config).run()
