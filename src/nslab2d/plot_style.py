"""Shared plotting style for documentation and publication-style figures.

The style choices are intentionally conservative and are based on widely used
scientific-figure guidance:

- use standard sans-serif fonts that render reliably on all platforms
- avoid decorative styling and heavy backgrounds
- prefer colorblind-safe categorical colors
- use perceptually sensible colormaps for scalar fields
- keep text dark gray rather than pure black for a slightly softer appearance

References that motivated the defaults include the Nature research figure guide,
Matplotlib's guidance on rcParams and colormaps, and common publication-quality
Matplotlib practice.
"""

from __future__ import annotations

from collections.abc import Sequence

import matplotlib as mpl

# Wong / Nature-style colorblind-safe qualitative palette.
WONG = {
    "black": "#000000",
    "orange": "#E69F00",
    "sky_blue": "#56B4E9",
    "bluish_green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "reddish_purple": "#CC79A7",
}

ACCENT_COLORS: tuple[str, ...] = (
    WONG["blue"],
    WONG["vermillion"],
    WONG["bluish_green"],
    WONG["reddish_purple"],
    WONG["orange"],
    WONG["sky_blue"],
)

TEXT_DARK = "#303030"
GRID_LIGHT = "#D9D9D9"
SPINE_LIGHT = "#666666"
SIGNED_CMAP = "RdBu_r"
SEQUENTIAL_CMAP = "cividis"


def apply_academic_plot_style() -> None:
    """Apply a shared Matplotlib style for academic/web-documentation figures."""
    mpl.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 220,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.prop_cycle": mpl.cycler(color=list(ACCENT_COLORS)),
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "Liberation Sans"],
            "font.size": 10.0,
            "axes.titlesize": 11.0,
            "axes.labelsize": 10.0,
            "legend.fontsize": 9.0,
            "xtick.labelsize": 9.0,
            "ytick.labelsize": 9.0,
            "text.color": TEXT_DARK,
            "axes.labelcolor": TEXT_DARK,
            "axes.edgecolor": SPINE_LIGHT,
            "axes.linewidth": 0.8,
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": TEXT_DARK,
            "ytick.color": TEXT_DARK,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 4.0,
            "ytick.major.size": 4.0,
            "xtick.minor.size": 2.5,
            "ytick.minor.size": 2.5,
            "lines.linewidth": 1.8,
            "lines.markersize": 5.0,
            "grid.color": GRID_LIGHT,
            "grid.linewidth": 0.6,
            "grid.alpha": 0.5,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "image.cmap": SEQUENTIAL_CMAP,
        }
    )


def add_light_ygrid(ax) -> None:
    """Add a light y-grid for quantitative line plots only."""
    ax.grid(True, axis="y", color=GRID_LIGHT, linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)


def categorical_colors(n: int) -> Sequence[str]:
    """Return the first ``n`` colors from the shared qualitative palette."""
    return ACCENT_COLORS[:n]
