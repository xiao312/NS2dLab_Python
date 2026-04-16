"""Diagnostics and derived fields for NS2dLab."""

from __future__ import annotations

from .backend import Backend


def gather_timeseries(U, V, KX, KY, dx: float, L: float, nu: float, backend: Backend):
    """Compute kinetic energy and dissipation rate for the current fields."""
    i = 1j
    fft2 = backend.fft2
    ifft2 = backend.ifft2
    real = backend.real
    xp = backend.xp

    ekin = 0.5 * xp.sum((U**2 + V**2) * dx * dx) / L**2

    dudx = real(ifft2(i * KX * fft2(U)))
    dudy = real(ifft2(i * KY * fft2(U)))
    dvdx = real(ifft2(i * KX * fft2(V)))
    dvdy = real(ifft2(i * KY * fft2(V)))

    diss = nu * xp.sum((dudx**2 + dudy**2 + dvdx**2 + dvdy**2) * dx * dx) / L**2
    return ekin, diss


def curl(U, V, KX, KY, backend: Backend):
    """Return the scalar z-vorticity / curl of the 2D velocity field."""
    i = 1j
    fft2 = backend.fft2
    ifft2 = backend.ifft2
    return backend.real(ifft2(i * KX * fft2(V))) - backend.real(ifft2(i * KY * fft2(U)))


def divergence(U, V, KX, KY, backend: Backend):
    """Return the divergence field used for incompressibility checks."""
    i = 1j
    fft2 = backend.fft2
    ifft2 = backend.ifft2
    return backend.real(ifft2(i * KX * fft2(U) + i * KY * fft2(V)))
