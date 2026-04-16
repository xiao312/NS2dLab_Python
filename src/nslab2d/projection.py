"""Helmholtz–Hodge projection used by NS2dLab."""

from __future__ import annotations

from .backend import Backend


def project(dU, dV, KX, KY, AA, backend: Backend):
    """Project a velocity-like field onto its divergence-free component.

    The implementation mirrors `project.m` and works both for full velocity fields
    and for Runge–Kutta increments.
    """
    xp = backend.xp
    FU = AA * backend.fft2(dU)
    FV = AA * backend.fft2(dV)
    # Keep the exact denominator floor used in MATLAB to avoid division by zero at
    # the zero mode while preserving the original numerical behavior.
    denom = xp.maximum(1e-10, KX**2 + KY**2)
    FUU = FU - (KX * FU + KY * FV) * KX / denom
    FVV = FV - (KX * FU + KY * FV) * KY / denom
    dU = backend.real(backend.ifft2(FUU))
    dV = backend.real(backend.ifft2(FVV))
    return dU, dV
