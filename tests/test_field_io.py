from __future__ import annotations

from pathlib import Path

import numpy as np

from nslab2d.field_io import load_velocity_field_npz, save_velocity_field_npz


def test_velocity_field_roundtrip(tmp_path: Path):
    U = np.arange(16, dtype=float).reshape(4, 4)
    V = -U
    path = tmp_path / "field.npz"
    save_velocity_field_npz(path, U=U, V=V, dx=0.1, metadata={"case": "demo"})
    loaded = load_velocity_field_npz(path)
    assert np.allclose(loaded["U"], U)
    assert np.allclose(loaded["V"], V)
    assert loaded["dx"] == 0.1
    assert loaded["dy"] == 0.1
