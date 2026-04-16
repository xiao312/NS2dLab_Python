"""Laminar flame properties from Cantera.

The main quantities needed for turbulent premixed-flame regime classification are
computed from a freely propagating 1D flame:

- laminar flame speed `S_L`
- thermal diffusivity thickness `delta_alpha = alpha_u / S_L`
- thermal-gradient thickness `delta_T = (T_b - T_u) / max(dT/dx)`

Two thickness definitions are reported because combustion-regime diagrams are sensitive
to how flame thickness is defined. The `delta_alpha` form is used as the default regime
thickness in this project because it aligns well with classical Borghi/Peters usage.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(slots=True)
class FlameProperties:
    """Laminar flame properties returned by the Cantera helper."""

    mechanism: str
    fuel: str
    oxidizer: str
    phi: float
    T_u: float
    P_u: float
    transport_model: str
    width: float
    S_L: float
    alpha_u: float
    delta_alpha: float
    delta_T: float
    T_b: float
    rho_u: float
    cp_u: float
    lambda_u: float
    grid_points: int


def _import_cantera():
    try:
        import cantera as ct
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Cantera is required for flame-property calculations. Install the optional "
            "combustion stack, e.g. `uv pip install -e '.[combustion]'`."
        ) from exc
    return ct


def compute_laminar_flame_properties(
    mechanism: str,
    fuel: str,
    oxidizer: str,
    phi: float,
    T_u: float,
    P_u: float,
    *,
    width: float = 0.03,
    transport_model: str = "mixture-averaged",
    loglevel: int = 0,
    refine_ratio: float = 3.0,
    refine_slope: float = 0.06,
    refine_curve: float = 0.12,
) -> FlameProperties:
    """Solve a freely propagating premixed flame and extract useful properties.

    Parameters follow standard Cantera practice. The `fuel` and `oxidizer` arguments are
    the same values you would pass to `gas.set_equivalence_ratio(...)`, e.g.

    - fuel: ``"CH4"``
    - oxidizer: ``"O2:1.0, N2:3.76"``
    """
    ct = _import_cantera()

    gas = ct.Solution(mechanism)
    gas.set_equivalence_ratio(phi, fuel, oxidizer)
    gas.TP = T_u, P_u

    rho_u = float(gas.density)
    cp_u = float(gas.cp_mass)
    lambda_u = float(gas.thermal_conductivity)
    alpha_u = lambda_u / (rho_u * cp_u)

    flame = ct.FreeFlame(gas, width=width)
    flame.transport_model = transport_model
    flame.set_refine_criteria(ratio=refine_ratio, slope=refine_slope, curve=refine_curve)
    flame.solve(loglevel=loglevel, auto=True)

    S_L = float(flame.velocity[0])
    T = np.asarray(flame.T, dtype=np.float64)
    grid = np.asarray(flame.grid, dtype=np.float64)
    dTdx = np.gradient(T, grid)
    T_b = float(np.max(T))
    delta_T = float((T_b - T_u) / np.max(np.abs(dTdx)))
    delta_alpha = float(alpha_u / S_L)

    return FlameProperties(
        mechanism=mechanism,
        fuel=fuel,
        oxidizer=oxidizer,
        phi=float(phi),
        T_u=float(T_u),
        P_u=float(P_u),
        transport_model=transport_model,
        width=float(width),
        S_L=S_L,
        alpha_u=float(alpha_u),
        delta_alpha=delta_alpha,
        delta_T=delta_T,
        T_b=T_b,
        rho_u=rho_u,
        cp_u=cp_u,
        lambda_u=lambda_u,
        grid_points=int(len(grid)),
    )


def flame_properties_to_dict(props: FlameProperties) -> dict[str, Any]:
    """Convert flame properties to a JSON-friendly dictionary."""
    return asdict(props)
