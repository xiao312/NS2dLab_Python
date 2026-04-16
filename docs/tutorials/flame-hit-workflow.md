# Generate a flame/HIT workflow example

This tutorial shows how to turn a turbulence field into a simple flame-workflow example.

## What you will do

You will:

1. generate a final velocity field snapshot
2. compute HIT statistics from the field
3. compute laminar flame properties with Cantera
4. place the case on a Borghi/Peters-style regime diagram
5. export an OpenFOAM `U` file

Estimated time: 10–20 minutes for the lighter example commands below.

## Prerequisites

- combustion dependencies installed
- package installed and virtual environment activated

## Step 1: generate a field snapshot

```bash
nslab2d run \
  --backend cpu \
  --N 128 \
  --dt 0.1 \
  --simutime-seconds 10 \
  --output results/tutorial_case.mat \
  --save-field-npz results/tutorial_case_field.npz
```

## Step 2: compute HIT statistics

```bash
nslab2d hit-stats --field-npz results/tutorial_case_field.npz
```

This reports quantities such as:

- mean velocity
- RMS turbulence intensity
- 2D turbulent kinetic energy
- integral length scale

## Step 3: compute flame properties

```bash
nslab2d flame-properties \
  --mechanism h2o2.yaml \
  --fuel H2 \
  --oxidizer 'O2:1.0, AR:5.0' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325
```

This computes:

- laminar flame speed `S_L`
- `delta_alpha`
- `delta_T`
- `alpha_u`

## Step 4: generate a regime diagram

```bash
nslab2d regime-diagram \
  --field-npz results/tutorial_case_field.npz \
  --mechanism h2o2.yaml \
  --fuel H2 \
  --oxidizer 'O2:1.0, AR:5.0' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325 \
  --output results/tutorial_regime.png
```

## Step 5: export to OpenFOAM

```bash
nslab2d export-openfoam-u \
  --field-npz results/tutorial_case_field.npz \
  --case-dir results/tutorial_openfoam_case \
  --time-dir 0 \
  --ordering x-fastest
```

## What you learned

You completed the full turbulence-to-combustion handoff path:

- generated a flow field
- measured turbulence statistics
- computed flame properties
- classified the case on a regime diagram
- exported a field to OpenFOAM format

## Next steps

- [Use the flame/HIT workflow guide](../how-to/use-the-flame-hit-workflow.md)
- [Read the flame/HIT explanation](../explanation/flame-hit-methodology.md)
- [Inspect flame/HIT results](../results/flame-hit-results.md)
