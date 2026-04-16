"""Field construction and RHS operators for NS2dLab.

These functions intentionally mirror the original MATLAB implementation.  The goal
is readability and numerical faithfulness, not aggressive refactoring.
"""

from __future__ import annotations

from math import pi

import numpy as np

from .backend import Backend
from .config import NS2dConfig
from .types import NS2dFields


def _meshgrid(xp, x, y):
    return xp.meshgrid(x, y)


def create_fields(config: NS2dConfig, backend: Backend) -> NS2dFields:
    """Create geometry, spectral operators, RK coefficients, and initial fields.

    The initialization follows `CreateFields.m` closely, including the exact
    MATLAB-style wave-number generation and the non-linear default vortex-array
    initial condition.
    """
    xp = backend.xp
    N = config.N
    nu = config.nu
    L = config.L
    dx = L / N

    x = (L - dx) * xp.arange(N, dtype=xp.float64) / (N - 1)
    y = (L - dx) * xp.arange(N, dtype=xp.float64) / (N - 1)
    X, Y = _meshgrid(xp, x, y)

    U = xp.zeros((N, N), dtype=xp.float64)
    V = xp.zeros((N, N), dtype=xp.float64)

    # Preserve the MATLAB wavenumber construction exactly rather than replacing
    # it with fftfreq-style helpers.  This keeps mode ordering/projection behavior
    # aligned with the original code.
    kx1 = xp.mod(0.5 + xp.arange(N, dtype=xp.float64) / N, 1.0) - 0.5
    ky1 = xp.mod(0.5 + xp.arange(N, dtype=xp.float64) / N, 1.0) - 0.5
    kx = kx1 * (2 * pi / dx)
    ky = ky1 * (2 * pi / dx)
    KX, KY = _meshgrid(xp, kx, ky)

    # 2/3-rule style anti-aliasing mask used in the nonlinear term and projection.
    AA = ((xp.abs(KX) < (2.0 / 3.0) * xp.max(kx)) * (xp.abs(KY) < (2.0 / 3.0) * xp.max(ky))).astype(xp.float64)

    a = backend.asarray(np.array([1 / 6, 1 / 3, 1 / 3, 1 / 6], dtype=np.float64), dtype=xp.float64)
    b = backend.asarray(np.array([0.5, 0.5, 1.0, 1.0], dtype=np.float64), dtype=xp.float64)

    # Default MATLAB initial condition: a non-linearized Taylor-Green-like vortex
    # array that quickly develops into a visually turbulent 2D field.
    Umax = 0.1
    kmax = 8
    U = -Umax * xp.cos(kmax * X) * xp.sin(kmax * Y)
    V = Umax * xp.sin(kmax * X) * xp.cos(kmax * Y)
    U = -Umax * xp.cos(kmax * X * V) * xp.sin(kmax * Y * U)
    V = Umax * xp.sin(kmax * X * U) * xp.cos(kmax * Y * V)

    from .projection import project

    U, V = project(U, V, KX, KY, AA, backend)

    return NS2dFields(X=X, Y=Y, U=U, V=V, KX=KX, KY=KY, AA=AA, a=a, b=b, dx=dx)


def compute_advection_skew(U, V, KX, KY, AA, dt: float, backend: Backend):
    """Compute the skew-symmetric advection increment.

    This ports `Compute2DadvectionSkew.m` term-by-term.  The result already
    includes the stage scaling by `dt/2` used in the MATLAB routine.
    """
    i = 1j
    fft2 = backend.fft2
    ifft2 = backend.ifft2
    real = backend.real

    dU = (
        -U * real(ifft2(i * KX * AA * fft2(U)))
        - V * real(ifft2(i * KY * AA * fft2(U)))
        - real(ifft2(i * KX * AA * fft2(U * U)))
        - real(ifft2(i * KY * AA * fft2(U * V)))
    ) * dt / 2.0

    dV = (
        -U * real(ifft2(i * KX * AA * fft2(V)))
        - V * real(ifft2(i * KY * AA * fft2(V)))
        - real(ifft2(i * KX * AA * fft2(U * V)))
        - real(ifft2(i * KY * AA * fft2(V * V)))
    ) * dt / 2.0

    return dU, dV


def compute_diffusion(U, V, KX, KY, nu: float, dt: float, backend: Backend):
    """Compute the spectral diffusion increment.

    Note that the original MATLAB code does not apply the anti-alias mask here;
    this behavior is preserved intentionally.
    """
    fft2 = backend.fft2
    ifft2 = backend.ifft2
    real = backend.real

    dU = nu * dt * (real(ifft2(-(KX * KX) * fft2(U))) + real(ifft2(-(KY * KY) * fft2(U))))
    dV = nu * dt * (real(ifft2(-(KX * KX) * fft2(V))) + real(ifft2(-(KY * KY) * fft2(V))))
    return dU, dV
