"""MATLAB-compatible IO helpers for NS2dLab outputs."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import loadmat, savemat

from .config import NS2dConfig
from .types import NS2dTimeseries


def _as_column(arr) -> np.ndarray:
    """Convert 1D-like data to an `N x 1` MATLAB-style column vector."""
    out = np.asarray(arr, dtype=np.float64)
    return out.reshape(-1, 1)


def save_timeseries(path: str | Path, config: NS2dConfig, ts: NS2dTimeseries) -> None:
    """Save the standard NS2dLab timeseries fields into a `.mat` file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    savemat(
        target,
        {
            "Ekin": _as_column(ts.Ekin),
            "Diss": _as_column(ts.Diss),
            "dt": np.array([[config.dt]], dtype=np.float64),
            "N": np.array([[config.N]], dtype=np.float64),
            "Time": _as_column(ts.Time),
            "ElapsedTime": np.array([[ts.ElapsedTime]], dtype=np.float64),
        },
        do_compression=True,
    )


def load_reference_timeseries(path: str | Path) -> dict[str, np.ndarray]:
    """Load non-private variables from a MATLAB `.mat` file."""
    raw = loadmat(path)
    return {k: v for k, v in raw.items() if not k.startswith("__")}


def compare_mat_timeseries(reference_path: str | Path, candidate_path: str | Path) -> dict[str, float]:
    """Compare common timeseries fields between two `.mat` files.

    The comparison is intentionally simple and returns max absolute error, max
    relative error, and RMSE for any shared standard fields.
    """
    ref = load_reference_timeseries(reference_path)
    cand = load_reference_timeseries(candidate_path)
    metrics: dict[str, float] = {}
    for key in ("Ekin", "Diss", "Time"):
        if key not in ref or key not in cand:
            continue
        ref_arr = np.asarray(ref[key], dtype=np.float64).reshape(-1)
        cand_arr = np.asarray(cand[key], dtype=np.float64).reshape(-1)
        common = min(ref_arr.size, cand_arr.size)
        ref_arr = ref_arr[:common]
        cand_arr = cand_arr[:common]
        diff = cand_arr - ref_arr
        denom = np.maximum(np.abs(ref_arr), 1e-16)
        metrics[f"{key}_max_abs"] = float(np.max(np.abs(diff)))
        metrics[f"{key}_max_rel"] = float(np.max(np.abs(diff) / denom))
        metrics[f"{key}_rmse"] = float(np.sqrt(np.mean(diff**2)))
    return metrics
