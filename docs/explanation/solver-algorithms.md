# Solver algorithms

This page explains the numerical method implemented by the solver.

The detailed algorithm notes remain in the original page:

- [NS2dLab algorithm notes](../algorithms.md)

In summary, the solver uses:

- a 2D incompressible Navier–Stokes formulation on a periodic square domain
- pseudo-spectral differentiation with full `fft2` / `ifft2`
- skew-symmetric advection
- explicit RK4 time stepping matching the MATLAB stage ordering
- Fourier-space Helmholtz–Hodge projection
- source-faithful wave-number generation and anti-aliasing semantics

This page is intentionally brief because the full explanation already exists in the linked algorithm notes.
