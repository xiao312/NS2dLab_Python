# Output formats

This page describes the main generated file formats used by the current workflows.

## MATLAB-style `.mat` timeseries output

The solver writes a MATLAB-friendly `.mat` file containing the main timeseries arrays:

- `Ekin`
- `Diss`
- `Time`
- `ElapsedTime`
- configuration metadata such as `N` and `dt`

Use this format for:

- comparison with other NS2dLab-style runs
- plotting timeseries diagnostics
- archival of standard solver output

## Velocity-field `.npz` snapshot

The `--save-field-npz` option writes a compact NumPy archive containing:

- `U`
- `V`
- `dx`
- `dy`
- optional metadata

Use this format for:

- HIT statistics
- flame-property and regime workflows
- OpenFOAM export

## JSON summaries

Several CLI commands can write JSON output, including:

- `hit-stats`
- `flame-properties`
- `regime-diagram`
- `validate-manuscript-cases`

Use JSON output for:

- reproducible records
- downstream plotting/reporting
- documentation artifact generation

## OpenFOAM `U` file

The OpenFOAM exporter writes a `volVectorField` containing cell-centered vectors of the form:

```text
(Ux Uy 0)
```

The caller must ensure that the chosen flattening order matches the target mesh cell ordering.
