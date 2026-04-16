# NS2dLab algorithm notes

This document summarizes the numerical algorithm implemented in `src/nslab2d/`.
It is intentionally close to the original MATLAB `NS2dLab` source.

## Governing equations

The solver advances the 2D incompressible Navier–Stokes equations on a periodic square domain:

- side length `L = 2π`
- velocity components `U(x,y,t)` and `V(x,y,t)`
- kinematic viscosity `ν`

The code uses a pseudo-spectral formulation:

- nonlinear products are evaluated in physical space
- derivatives are evaluated in Fourier space
- incompressibility is enforced by projection in Fourier space

## Spatial discretization

### Grid

The domain is discretized on an `N x N` uniform grid.
Variables live at cell-centre-like locations on the periodic lattice, following the MATLAB implementation.

### Wave numbers

The wave-number arrays are generated using the same MATLAB-style formula as the original code instead of replacing them with `numpy.fft.fftfreq`.
This preserves indexing and projection behavior more faithfully.

### Anti-aliasing

The nonlinear term uses a 2/3-rule style anti-alias mask:

- `AA = 1` for retained modes
- `AA = 0` for filtered modes

This mask is applied in the advection term and in the projection routine.

## Time integration

Time integration follows the original explicit four-stage Runge–Kutta formulation used in `SolveNavierStokes2D.m`.

For each RK stage:

1. compute the skew-symmetric advection increment
2. compute the diffusion increment
3. add the increments
4. project the increment to divergence-free form
5. update the stage state using the original MATLAB `a` / `b` coefficients

A final projection is applied after the RK accumulation.

## Advection term

The advection operator is ported from `Compute2DadvectionSkew.m`.
It uses the skew-symmetric formulation because it is more stable and better behaved for turbulence-like calculations than a naive convective form.

## Diffusion term

The diffusion operator is ported from `Compute2Ddiffusion.m`.
It evaluates the Laplacian spectrally using the wave numbers `KX` and `KY`.

## Projection method

The projection is ported from `project.m`.

The velocity field is transformed into Fourier space and the component parallel to the wave vector is removed. This is the Fourier-space Helmholtz–Hodge projection.

A small denominator floor `1e-10` is preserved exactly from MATLAB to avoid division by zero at the zero mode.

## Diagnostics

The solver computes the same main timeseries diagnostics as the MATLAB code:

### Kinetic energy

`Ekin(t)` is computed from the domain integral of `0.5 * (U^2 + V^2)`.

### Dissipation rate

`Diss(t)` is computed pseudo-spectrally from velocity gradients.

## Backends

The solver implementation is shared between backends.
Only the array/FFT backend differs.

### CPU backend

- NumPy arrays
- PyFFTW-backed `fft2` / `ifft2`
- reference backend for correctness

### GPU backend

- CuPy arrays
- CuPy FFT routines
- optional, imported lazily

## Validation cases currently used

- default vortex-array case from the original NS2dLab setup
- Taylor–Green vortex analytical solution
- 2D pseudo-turbulence energy identity check
