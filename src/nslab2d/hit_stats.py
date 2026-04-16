"""Homogeneous isotropic turbulence (HIT) statistics from 2D NS2dLab fields.

The functions in this module turn a 2D velocity field into the quantities most often
needed for premixed turbulent-flame regime classification:

- mean velocity
- fluctuating velocity RMS values
- turbulent kinetic energy
- integral length scale estimated from periodic two-point correlations

The implementation is intentionally simple and explicit so new users can audit the
calculations quickly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class HITStats:
    """Summary statistics extracted from a 2D velocity field.

    Notes
    -----
    `uprime_component_rms` is the default turbulence intensity recommended for
    regime-diagram placement. It is defined as

        sqrt(<u'^2 + v'^2> / 2)

    which mirrors the component-wise RMS convention often used in turbulence and
    premixed-combustion literature.
    """

    mean_u: float
    mean_v: float
    uprime_component_rms: float
    uprime_planar_rms: float
    tke_2d: float
    integral_length_scale_x: float
    integral_length_scale_y: float
    integral_length_scale_mean: float
    dx: float
    dy: float


def _periodic_longitudinal_autocorrelation(field: np.ndarray, axis: int) -> np.ndarray:
    """Compute a periodic longitudinal autocorrelation by direct averaging.

    For lag `k`, the correlation is

        R(k) = <f(i) f(i+k)>

    with periodic wrap-around and averaging over all points in the orthogonal direction.
    The output length equals the number of grid points along the chosen axis.
    """
    n = field.shape[axis]
    corr = np.empty(n, dtype=np.float64)
    for lag in range(n):
        shifted = np.roll(field, -lag, axis=axis)
        corr[lag] = float(np.mean(field * shifted))
    return corr


def _integral_scale_from_correlation(corr: np.ndarray, spacing: float) -> float:
    """Integrate the normalized correlation up to its first zero crossing.

    This is a practical definition of integral length scale for periodic HIT fields.
    If the correlation does not cross zero in the usable half-domain, the integration is
    carried out over the entire available half-range.
    """
    half = corr[: corr.size // 2 + 1]
    r = np.arange(half.size, dtype=np.float64) * spacing
    if np.isclose(half[0], 0.0):
        return 0.0
    norm = half / half[0]

    zero_idx = None
    for idx in range(1, norm.size):
        if norm[idx] <= 0.0:
            zero_idx = idx
            break

    if zero_idx is None:
        return float(np.trapezoid(norm, r))

    # Interpolate linearly to estimate where the first zero crossing occurs.
    x0, x1 = r[zero_idx - 1], r[zero_idx]
    y0, y1 = norm[zero_idx - 1], norm[zero_idx]
    if np.isclose(y1, y0):
        x_zero = x1
    else:
        x_zero = x0 - y0 * (x1 - x0) / (y1 - y0)

    r_used = np.concatenate([r[:zero_idx], np.array([x_zero])])
    norm_used = np.concatenate([norm[:zero_idx], np.array([0.0])])
    return float(np.trapezoid(norm_used, r_used))


def compute_hit_stats(U: np.ndarray, V: np.ndarray, dx: float, dy: float | None = None) -> HITStats:
    """Compute turbulence statistics from a 2D velocity field.

    Parameters
    ----------
    U, V:
        2D cell-centered velocity components.
    dx, dy:
        Grid spacing in the x and y directions. If `dy` is omitted it is assumed equal to
        `dx`.
    """
    if dy is None:
        dy = dx

    U = np.asarray(U, dtype=np.float64)
    V = np.asarray(V, dtype=np.float64)

    mean_u = float(np.mean(U))
    mean_v = float(np.mean(V))
    u = U - mean_u
    v = V - mean_v

    uprime_component_rms = float(np.sqrt(np.mean(u**2 + v**2) / 2.0))
    uprime_planar_rms = float(np.sqrt(np.mean(u**2 + v**2)))
    tke_2d = float(0.5 * np.mean(u**2 + v**2))

    corr_x = _periodic_longitudinal_autocorrelation(u, axis=1)
    corr_y = _periodic_longitudinal_autocorrelation(v, axis=0)
    lint_x = _integral_scale_from_correlation(corr_x, dx)
    lint_y = _integral_scale_from_correlation(corr_y, dy)

    return HITStats(
        mean_u=mean_u,
        mean_v=mean_v,
        uprime_component_rms=uprime_component_rms,
        uprime_planar_rms=uprime_planar_rms,
        tke_2d=tke_2d,
        integral_length_scale_x=lint_x,
        integral_length_scale_y=lint_y,
        integral_length_scale_mean=0.5 * (lint_x + lint_y),
        dx=float(dx),
        dy=float(dy),
    )
