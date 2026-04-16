# Flame-in-HIT workflow

This document explains the intended combustion-facing workflow for `NS2dLab_Python`.

## Use case

The package is used to generate a fully developed 2D turbulent velocity field with
`NS2dLab`, and then reuse that field as the initial flow field for a premixed-flame case,
for example:

- square 2D domain
- stoichiometric fuel/air mixture
- central hot ignition kernel
- transition from ignition to flame propagation in 2D HIT

## Step 1: generate the turbulent field

Run the solver and save a field snapshot:

```bash
nslab2d run --backend cpu --N 256 --dt 0.05 --simutime-seconds 50 \
  --output results/VortexArray2d_256.mat --save-field-npz results/VortexArray2d_256_field.npz
```

The `.mat` file stores the NS2dLab timeseries. The `.npz` file stores the full velocity
field and grid spacing for downstream analysis/export.

## Step 2: compute HIT statistics

```bash
nslab2d hit-stats --field-npz results/VortexArray2d_256_field.npz
```

This reports:

- mean velocity
- component RMS turbulence intensity
- planar RMS turbulence intensity
- 2D turbulent kinetic energy
- integral length scales in x and y
- mean integral length scale

The default turbulence intensity used for the flame regime diagram is the component RMS
value.

## Step 3: compute laminar flame properties with Cantera

```bash
nslab2d flame-properties \
  --mechanism gri30.yaml \
  --fuel CH4 \
  --oxidizer 'O2:1.0, N2:3.76' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325
```

This solves a freely propagating 1D flame and reports:

- laminar flame speed `S_L`
- thermal-diffusivity thickness `delta_alpha = alpha_u / S_L`
- thermal-gradient thickness `delta_T`
- unburned thermal diffusivity `alpha_u`
- burned gas temperature estimate `T_b`

## Step 4: place the case on a turbulent flame regime diagram

```bash
nslab2d regime-diagram \
  --field-npz results/VortexArray2d_256_field.npz \
  --mechanism gri30.yaml \
  --fuel CH4 \
  --oxidizer 'O2:1.0, N2:3.76' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325 \
  --output artifacts/regime_diagram.png
```

The diagram uses:

- x-axis: `l_t / delta_L`
- y-axis: `u' / S_L`

and also reports:

- `Da`
- `Ka`

Important: the Borghi/Peters-style diagram is classically a 3D turbulent premixed-flame
classification tool. When applied to a 2D HIT field, the result should be interpreted as a
useful **approximate** classification, not a strict 3D equivalence.

## Step 5: export the velocity field to OpenFOAM 7

```bash
nslab2d export-openfoam-u \
  --field-npz results/VortexArray2d_256_field.npz \
  --case-dir /path/to/openfoam_case \
  --time-dir 0 \
  --ordering x-fastest
```

This writes a `volVectorField` named `U` to the chosen OpenFOAM time directory.

## OpenFOAM ordering note

The exporter writes cell-centered vectors in the requested flattening order. The caller
must make sure that this ordering matches the target OpenFOAM mesh cell ordering.

Available options:

- `x-fastest`
- `y-fastest`

## Boundary conditions note

The exporter only writes the field file; it does not generate a mesh.

A minimal default boundary dictionary is used if no boundary JSON file is supplied.
For realistic cases, pass an explicit boundary description that matches your OpenFOAM
mesh patches.

## Recommended practice

For each flame case, archive:

- the NS2dLab field snapshot (`.npz`)
- the flame-property JSON
- the regime-diagram JSON + PNG
- the OpenFOAM `U` file used for the CFD case

That makes the full flow-to-flame initialization chain reproducible.
