# Unified figure style

All generated figures shown in this documentation site use a shared plotting style implemented in
`src/nslab2d/plot_style.py`.

## Design goals

The style was chosen to match common academic-figure guidance:

- **standard sans-serif fonts** for reliable rendering on web and in exported vector files
- **colorblind-safe categorical colors** based on the Wong / Nature-style accessible palette
- **perceptually sensible colormaps** for scalar fields
- **minimal decoration**: no heavy backgrounds, no top/right spines, and only light grids when they aid reading
- **editable vector-friendly text settings** via `pdf.fonttype = 42` and `svg.fonttype = none`

## Sources that informed the style

The selected defaults were guided by:

- Nature Research figure guidance, especially accessible color use, standard fonts, and avoiding decorative clutter
- Matplotlib's official guidance on rcParams, style sheets, and colormap selection
- common publication-quality scientific plotting practice emphasizing reproducibility and colorblind-safe palettes

## Selected visual language

### Typography

- Font family: `DejaVu Sans`, with Arial/Helvetica-style fallbacks
- Small but readable academic sizing for labels, ticks, and legends
- Dark gray text rather than harsh pure black for less visual fatigue

### Colors

For categorical lines/bars, the project uses an accessible palette with examples such as:

- blue `#0072B2`
- vermillion `#D55E00`
- bluish green `#009E73`
- reddish purple `#CC79A7`
- orange `#E69F00`
- sky blue `#56B4E9`

### Colormaps

- **Sequential fields**: `cividis`
- **Signed / zero-centered fields** such as vorticity: `RdBu_r`

### Layout conventions

- white background
- left/bottom spines only
- outward ticks
- light y-grid only for quantitative comparison plots
- no legend boxes unless necessary

## Why this matters

A consistent style makes the project easier to read and compare:

- validation plots look like they belong to the same codebase
- CPU/GPU comparison charts are immediately recognizable
- flame/HIT results can be dropped into reports or manuscripts with minimal restyling
- generated figures remain reproducible directly from Python

## Regenerating styled figures

The documentation assets are generated with:

```bash
python scripts/generate_docs_artifacts.py
```

This script runs the main feature set, collects outputs under `docs/assets/generated/`, and applies the shared style automatically.
