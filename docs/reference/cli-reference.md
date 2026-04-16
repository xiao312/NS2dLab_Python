# CLI reference

The package exposes one command-line entry point:

```bash
nslab2d <command> [options]
```

## Core solver commands

### `run`

Run the NS2dLab solver and save a MATLAB-style output file.

Common options:

- `--backend {cpu,gpu}`
- `--N`
- `--dt`
- `--simutime-seconds`
- `--nu`
- `--output`
- `--save-field-npz`

### `compare-reference`

Compare two NS2dLab-style `.mat` files.

Required options:

- `--reference`
- `--candidate`

## Backend commands

### `device-info`

Report whether a GPU is available and, if so, print device metadata.

### `compare-backends`

Run the same case on CPU and GPU and compare timeseries and final fields.

### `benchmark`

Benchmark one backend across multiple grid sizes.

Required options:

- `--backend`
- `--N`
- `--dt`

### `validate-manuscript-cases`

Run the heavier manuscript-scale CPU↔GPU validation set.

## Flame/HIT commands

### `hit-stats`

Compute turbulence statistics from a saved field snapshot.

Required options:

- `--field-npz`

### `flame-properties`

Compute laminar flame properties with Cantera.

Required options:

- `--mechanism`
- `--fuel`
- `--oxidizer`
- `--phi`
- `--Tu`
- `--Pu`

### `regime-diagram`

Compute a regime point and render a Borghi/Peters-style plot.

Required options:

- `--field-npz`
- flame-property arguments
- `--output`

### `export-openfoam-u`

Export a saved field to an OpenFOAM 7 `U` file.

Required options:

- `--field-npz`
- `--case-dir`

## Related pages

- [Run your first simulation](../tutorials/run-your-first-simulation.md)
- [Use the flame/HIT workflow](../how-to/use-the-flame-hit-workflow.md)
- [API reference](api-reference.md)
