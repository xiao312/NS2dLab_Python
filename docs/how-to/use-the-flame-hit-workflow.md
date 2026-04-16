# Use the flame/HIT workflow

Use this guide when you already know the basic workflow and want the exact command sequence for a reusable turbulence-to-combustion handoff.

## Generate a field snapshot

```bash
nslab2d run \
  --backend cpu \
  --N 256 \
  --dt 0.05 \
  --simutime-seconds 50 \
  --output results/VortexArray2d_256.mat \
  --save-field-npz results/VortexArray2d_256_field.npz
```

## Compute HIT statistics

```bash
nslab2d hit-stats --field-npz results/VortexArray2d_256_field.npz --output results/hit_stats.json
```

## Compute laminar flame properties

```bash
nslab2d flame-properties \
  --mechanism gri30.yaml \
  --fuel CH4 \
  --oxidizer 'O2:1.0, N2:3.76' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325 \
  --output results/flame_properties.json
```

## Generate a regime diagram

```bash
nslab2d regime-diagram \
  --field-npz results/VortexArray2d_256_field.npz \
  --mechanism gri30.yaml \
  --fuel CH4 \
  --oxidizer 'O2:1.0, N2:3.76' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325 \
  --output results/regime_diagram.png \
  --json-output results/regime_diagram.json
```

## Export an OpenFOAM field

```bash
nslab2d export-openfoam-u \
  --field-npz results/VortexArray2d_256_field.npz \
  --case-dir /path/to/openfoam_case \
  --time-dir 0 \
  --ordering x-fastest
```

## Archive the workflow outputs

For reproducibility, keep at least:

- the `.npz` field snapshot
- HIT statistics JSON
- flame-properties JSON
- regime-diagram JSON + image
- exported OpenFOAM `U` file
