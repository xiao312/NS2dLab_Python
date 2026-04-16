# NS2dLab Python backend design/spec

## Scope

This spec covers only the DNSLab `NS2dLab` solver.

Primary goals:

1. Match MATLAB source semantics as closely as possible.
2. Provide a fast CPU backend.
3. Provide an optional NVIDIA GPU backend.
4. Keep one shared solver implementation so CPU/GPU differences are isolated.

## MATLAB source contract

The Python port is derived from the published NS2dLab MATLAB algorithm and its documented routines:

- `NS2dLab.m`
- `SetParameters.m`
- `CreateFields.m`
- `Compute2DadvectionSkew.m`
- `Compute2Ddiffusion.m`
- `project.m`
- `SolveNavierStokes2D.m`
- `GatherTimeseries.m`
- `SaveTimeseries.m`

Porting rules:

- Preserve double precision (`float64`) everywhere.
- Preserve complex spectral math (`complex128`) everywhere.
- Preserve full `fft2`/`ifft2` behavior; do not switch to `rfft2`.
- Preserve exact wave-number generation and anti-alias mask formulas.
- Preserve the exact RK4 stage update order.
- Preserve the final projection step.
- Preserve diagnostics formulas and output names.
- Do not use fast-math or algebraic rearrangements in the reference CPU path.

## Backend abstraction

The solver has one computational backend object and one solver implementation.
The backend object owns array-module and FFT details.

### Interface

```python
class Backend:
    name: str
    xp: module-like array namespace

    def asarray(self, obj, dtype=None): ...
    def zeros(self, shape, dtype): ...
    def fft2(self, arr): ...
    def ifft2(self, arr): ...
    def real(self, arr): ...
    def to_numpy(self, arr): ...
    def synchronize(self): ...
```

### CPU backend

- `xp = numpy`
- FFT implementation = PyFFTW through cached NumPy-compatible interfaces
- `fft2` and `ifft2` return complex128 arrays
- `synchronize()` is a no-op

Rationale:

- easiest path to MATLAB-like semantics
- fast for repeated same-shape transforms
- reference backend for correctness

### GPU backend

- `xp = cupy`
- FFT implementation = `cupy.fft.fft2`, `cupy.fft.ifft2`
- `synchronize()` calls the current stream/device synchronize
- imported lazily so CPU-only installations still work

Rationale:

- NS2dLab is dominated by 2D FFT + pointwise operations
- this maps well to NVIDIA GPUs

## Shared solver data model

### `NS2dConfig`

Immutable runtime configuration.

Fields:

- `N: int`
- `dt: float`
- `simutime_seconds: float`
- `nu: float = 1e-4`
- `L: float = 2*pi`
- `visualize: bool = False`
- `backend: str = "cpu"`
- `fftw_threads: int | None = None`

Derived:

- `simutime_steps = round(simutime_seconds / dt)`

### `NS2dFields`

Physical and spectral fields allocated on backend.

Fields:

- `X, Y`
- `U, V`
- `KX, KY`
- `AA`
- `a, b` (RK coefficients)
- `dx`

### `NS2dTimeseries`

Saved diagnostics.

Fields:

- `Ekin: (steps,)`
- `Diss: (steps,)`
- `Time: (steps,)`
- `ElapsedTime: float`

## Initialization spec

Port `CreateFields.m` literally.

### Grid

```python
x = (L - dx) * np.arange(N) / (N - 1)
y = (L - dx) * np.arange(N) / (N - 1)
X, Y = meshgrid(x, y)
```

### Wave numbers

```python
kx1 = mod(0.5 + arange(N)/N, 1) - 0.5
ky1 = mod(0.5 + arange(N)/N, 1) - 0.5
kx = kx1 * (2*pi/dx)
ky = ky1 * (2*pi/dx)
KX, KY = meshgrid(kx, ky)
```

This is intentionally not replaced with `fftfreq` in the reference design.

### Anti-alias mask

```python
AA = ((abs(KX) < (2/3) * max(kx)) * (abs(KY) < (2/3) * max(ky))).astype(float64)
```

### Initial velocity

Port exactly:

```python
U = -Umax*cos(kmax*X)*sin(kmax*Y)
V =  Umax*sin(kmax*X)*cos(kmax*Y)
U = -Umax*cos(kmax*X*V)*sin(kmax*Y*U)
V =  Umax*sin(kmax*X*U)*cos(kmax*Y*V)
```

Then project to divergence-free.

## Solver step spec

Port `SolveNavierStokes2D.m` literally.

For each RK stage:

1. compute skew-symmetric advection increment
2. compute diffusion increment
3. sum increments
4. project increment
5. update stage state using `a`, `b`

Then:

- assign `U = Uc`, `V = Vc`
- apply final projection

## Advection spec

Port `Compute2DadvectionSkew.m` literally.

All Fourier transforms use backend `fft2/ifft2`.
Every inverse transform is wrapped in `real(...)`.

## Diffusion spec

Port `Compute2Ddiffusion.m` literally.

Note: the MATLAB code does **not** multiply by `AA` in diffusion.
The Python port preserves that behavior.

## Projection spec

Port `project.m` literally.

Key detail:

```python
denom = maximum(1e-10, KX**2 + KY**2)
```

This exact floor is preserved.

## Diagnostics spec

Port `GatherTimeseries.m` literally.

### Kinetic energy

```python
Ekin[t] = 0.5 * sum((U**2 + V**2) * dx * dx) / L**2
```

### Dissipation

Use spectral derivatives from `fft2` and `ifft2` exactly as in MATLAB.

## IO spec

### Saved outputs

Match MATLAB save names:

- `Ekin`
- `Diss`
- `dt`
- `N`
- `Time`
- `ElapsedTime`

### Format

- use `scipy.io.savemat`
- save arrays as column vectors where appropriate for MATLAB compatibility

## Validation spec

### Level 1: unit-level

- exact wave-number generation
- exact AA mask generation
- projection outputs divergence-free field
- CPU and GPU backend match on short runs

### Level 2: backend-equivalence checks

Primary regression targets:

- `Ekin`
- `Diss`
- final `U` field
- final `V` field

CPU and GPU runs should agree closely for the same configuration.

### Level 3: paper-level

When NS2dLab figures are identified/digitized from the DNSLab paper, compare:

- kinetic energy history
- dissipation history
- curl snapshots

## Performance policy

### CPU

First implementation priority:

- correctness
- PyFFTW caching
- double precision

Potential later tuning:

- explicit PyFFTW plans/builders
- FFTW wisdom import/export
- tuned thread count

### GPU

First implementation priority:

- all arrays stay on device inside timestep loop
- double precision
- CPU/GPU consistency with same formulas

Potential later tuning:

- CuPy plan cache inspection
- reduced host-device transfers

## Non-goals for v1

- no mixed precision
- no Numba kernels in core solver
- no sparse 3D solver work
- no API generalization beyond NS2dLab needs
