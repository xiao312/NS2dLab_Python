"""Simple field snapshot IO used by the combustion/HIT workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def save_velocity_field_npz(path: str | Path, *, U: np.ndarray, V: np.ndarray, dx: float, dy: float | None = None, metadata: dict[str, Any] | None = None) -> None:
    """Save a 2D velocity field and grid spacing into a compact `.npz` file."""
    if dy is None:
        dy = dx
    payload: dict[str, Any] = {
        "U": np.asarray(U, dtype=np.float64),
        "V": np.asarray(V, dtype=np.float64),
        "dx": np.array(dx, dtype=np.float64),
        "dy": np.array(dy, dtype=np.float64),
    }
    if metadata is not None:
        payload["metadata_json"] = np.array(str(metadata), dtype=object)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez(target, **payload)


def load_velocity_field_npz(path: str | Path) -> dict[str, Any]:
    """Load a velocity field saved by :func:`save_velocity_field_npz`."""
    data = np.load(path, allow_pickle=True)
    return {
        "U": np.asarray(data["U"], dtype=np.float64),
        "V": np.asarray(data["V"], dtype=np.float64),
        "dx": float(np.asarray(data["dx"])),
        "dy": float(np.asarray(data["dy"])),
        "metadata_json": data["metadata_json"].item() if "metadata_json" in data else None,
    }
