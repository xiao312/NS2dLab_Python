"""Configuration objects for NS2dLab."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi


@dataclass(frozen=True, slots=True)
class NS2dConfig:
    """Immutable run configuration for the 2D solver."""
    N: int = 2**7
    dt: float = 0.1
    simutime_seconds: float = 50.0
    nu: float = 1e-4
    L: float = 2 * pi
    visualize: bool = False
    backend: str = "cpu"
    fftw_threads: int | None = None
    fftw_cache_enable: bool = True

    @property
    def simutime_steps(self) -> int:
        return round(self.simutime_seconds / self.dt)

    @property
    def case_name(self) -> str:
        return f"VortexArray2d_{self.N}"
