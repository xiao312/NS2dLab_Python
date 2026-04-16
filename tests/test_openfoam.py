from __future__ import annotations

from pathlib import Path

import numpy as np

from nslab2d.openfoam import write_openfoam_u_file


def test_openfoam_u_writer_creates_expected_file(tmp_path: Path):
    U = np.array([[1.0, 2.0], [3.0, 4.0]])
    V = np.array([[5.0, 6.0], [7.0, 8.0]])
    out = write_openfoam_u_file(U, V, case_dir=tmp_path, time_dir="0", ordering="x-fastest")
    text = out.read_text(encoding="utf-8")
    assert "class volVectorField;" in text
    assert "dimensions [0 1 -1 0 0 0 0];" in text
    assert "internalField nonuniform List<vector>" in text
    assert "(1.0000000000000000e+00 5.0000000000000000e+00 0.0000000000000000e+00)" in text
    assert "frontAndBack" in text
