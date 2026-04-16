"""Simple typed containers used by NS2dLab."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class NS2dFields:
    """Mutable physical and spectral field bundle."""
    X: Any
    Y: Any
    U: Any
    V: Any
    KX: Any
    KY: Any
    AA: Any
    a: Any
    b: Any
    dx: float


@dataclass(slots=True)
class NS2dTimeseries:
    """Diagnostic timeseries collected during a simulation run."""
    Ekin: Any
    Diss: Any
    Time: Any
    ElapsedTime: float = 0.0
