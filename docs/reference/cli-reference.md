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

### `regime-targets`

Compute target turbulence values from a desired regime-diagram point.

Required options:

- `--Sl`
- `--deltaL`
- `--lt-over-deltaL`
- `--uprime-over-Sl`

### `tune-regime-field`

Generate and optionally evolve a divergence-free random field toward target `u'` and `l_t`.

You can provide targets in either of two ways:

- direct `--Sl` and `--deltaL`
- a full flame-property input set from which `S_L` and `delta_L` are computed

Optional search controls include:

- `--N-values` for a comma-separated search list such as `128,256,512,1024`
- `--L-values` for a comma-separated domain-length search list
- `--k0-values` for the spectral-peak search list
- `--mode-values` for a modal-index search list; when present, the code uses `k0 = m (2\pi/L)` for each tested `L`
- `--bandwidth-modes` for Gaussian bandwidth in modal-index units when using `--mode-values`

Optional outputs include:

- a tuning-history JSON through `--output-json`
- a search plot through `--output-search-plot`
- a reusable artifact bundle through `--output-artifacts-dir`, containing final curl, top-history curl montage, and regime-diagram history plots

### `target-regime-point`

Convenience command that tunes a field and writes a requested-vs-achieved search plot.
It also supports `--output-artifacts-dir` for publication-style visual summaries of the final field and search history.

## Related pages

- [Run your first simulation](../tutorials/run-your-first-simulation.md)
- [Use the flame/HIT workflow](../how-to/use-the-flame-hit-workflow.md)
- [API reference](api-reference.md)
