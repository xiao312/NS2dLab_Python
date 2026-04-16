# CLI guide

The package exposes a single command-line entry point:

```bash
nslab2d <command> [options]
```

This page summarizes the most important commands and how they fit together.

## Core solver commands

### `run`

Run the NS2dLab solver.

```bash
nslab2d run \
  --backend cpu \
  --N 128 \
  --dt 0.1 \
  --simutime-seconds 50 \
  --output results/VortexArray2d_128.mat
```

Optional field snapshot output:

```bash
nslab2d run ... --save-field-npz results/field.npz
```

### `compare-reference`

Compare two MATLAB-style `.mat` output files:

```bash
nslab2d compare-reference --reference a.mat --candidate b.mat
```

## Backend and performance commands

### `device-info`

Print GPU availability and device metadata.

```bash
nslab2d device-info
```

### `compare-backends`

Run the same short case on CPU and GPU and compare their outputs:

```bash
nslab2d compare-backends --N 64 --dt 0.1 --simutime-seconds 2
```

### `benchmark`

Benchmark one backend over several grid sizes:

```bash
nslab2d benchmark --backend cpu --N 64,128,256 --dt 0.1,0.1,0.05 --simutime-seconds 5
```

### `validate-manuscript-cases`

Run the heavier CPU↔GPU comparisons used for release-scale validation:

```bash
nslab2d validate-manuscript-cases --output results/manuscript_gpu_validation.json
```

## Flame/HIT workflow commands

### `hit-stats`

Compute turbulence statistics from a saved field snapshot:

```bash
nslab2d hit-stats --field-npz results/field.npz
```

### `flame-properties`

Compute laminar flame properties with Cantera:

```bash
nslab2d flame-properties \
  --mechanism gri30.yaml \
  --fuel CH4 \
  --oxidizer 'O2:1.0, N2:3.76' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325
```

### `regime-diagram`

Combine HIT statistics and laminar flame properties and render a Borghi/Peters-style
regime diagram:

```bash
nslab2d regime-diagram \
  --field-npz results/field.npz \
  --mechanism gri30.yaml \
  --fuel CH4 \
  --oxidizer 'O2:1.0, N2:3.76' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325 \
  --output artifacts/regime.png
```

### `export-openfoam-u`

Export a saved velocity field to an OpenFOAM 7 `U` file:

```bash
nslab2d export-openfoam-u \
  --field-npz results/field.npz \
  --case-dir /path/to/openfoam_case \
  --time-dir 0 \
  --ordering x-fastest
```

## Recommended command sequence for new users

1. `nslab2d run`
2. `nslab2d hit-stats`
3. `nslab2d flame-properties`
4. `nslab2d regime-diagram`
5. `nslab2d export-openfoam-u`

That sequence covers the full turbulence-to-combustion handoff workflow.
