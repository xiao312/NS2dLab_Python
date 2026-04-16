"""OpenFOAM 7 velocity-field export helpers.

The main use case is exporting a fully evolved NS2dLab 2D velocity field as a
`volVectorField` named `U` for an existing OpenFOAM 7 case.

This module intentionally targets a simple, explicit workflow:

1. the user already has a 2D structured OpenFOAM case
2. the internal cell count matches the NS2dLab field shape
3. the 2D field is exported with zero z-velocity
4. the boundary dictionaries are supplied by the caller or use a minimal default

The exporter does not attempt to generate a mesh. It only writes the field file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def _flatten_field(U: np.ndarray, V: np.ndarray, ordering: str) -> np.ndarray:
    """Flatten 2D fields into a list of OpenFOAM vectors.

    Parameters
    ----------
    ordering:
        - ``"x-fastest"``: flatten with x varying fastest in the output list
        - ``"y-fastest"``: flatten with y varying fastest in the output list
    """
    U = np.asarray(U, dtype=np.float64)
    V = np.asarray(V, dtype=np.float64)
    if U.shape != V.shape:
        raise ValueError("U and V must have the same shape")

    if ordering == "x-fastest":
        u_flat = U.reshape(-1, order="C")
        v_flat = V.reshape(-1, order="C")
    elif ordering == "y-fastest":
        u_flat = U.T.reshape(-1, order="C")
        v_flat = V.T.reshape(-1, order="C")
    else:
        raise ValueError(f"Unknown ordering: {ordering}")

    vectors = np.column_stack([u_flat, v_flat, np.zeros_like(u_flat)])
    return vectors


def default_boundary_field_dict() -> dict[str, dict[str, Any]]:
    """Return a conservative default boundary dictionary for 2D OpenFOAM cases."""
    return {
        "frontAndBack": {"type": "empty"},
    }


def _format_boundary_patch(name: str, data: dict[str, Any]) -> str:
    lines = [f"    {name}", "    {"]
    for key, value in data.items():
        if isinstance(value, str):
            lines.append(f"        {key} {value};")
        else:
            lines.append(f"        {key} {value};")
    lines.append("    }")
    return "\n".join(lines)


def write_openfoam_u_file(
    U: np.ndarray,
    V: np.ndarray,
    *,
    case_dir: str | Path,
    time_dir: str = "0",
    object_name: str = "U",
    ordering: str = "x-fastest",
    boundary_patches: dict[str, dict[str, Any]] | None = None,
) -> Path:
    """Write an OpenFOAM 7 `volVectorField` file for the velocity field.

    Parameters
    ----------
    U, V:
        2D NS2dLab velocity components.
    case_dir:
        Root of the OpenFOAM case.
    time_dir:
        Time directory to write into, typically ``"0"`` or another restart time.
    ordering:
        Structured flattening convention. The caller must ensure this matches the target
        mesh cell ordering.
    boundary_patches:
        Boundary dictionary entries to include under `boundaryField`.
    """
    vectors = _flatten_field(U, V, ordering=ordering)
    case_path = Path(case_dir)
    target_dir = case_path / time_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / object_name

    patches = default_boundary_field_dict() if boundary_patches is None else boundary_patches
    patch_block = "\n".join(_format_boundary_patch(name, spec) for name, spec in patches.items())

    with target.open("w", encoding="utf-8") as f:
        f.write("FoamFile\n")
        f.write("{\n")
        f.write("    version 2.0;\n")
        f.write("    format ascii;\n")
        f.write("    class volVectorField;\n")
        f.write(f'    location "{time_dir}";\n')
        f.write(f"    object {object_name};\n")
        f.write("}\n\n")
        f.write("dimensions [0 1 -1 0 0 0 0];\n\n")
        f.write("internalField nonuniform List<vector>\n")
        f.write(f"{len(vectors)}\n")
        f.write("(\n")
        for ux, vy, wz in vectors:
            f.write(f"({ux:.16e} {vy:.16e} {wz:.16e})\n")
        f.write(")\n;\n\n")
        f.write("boundaryField\n")
        f.write("{\n")
        if patch_block:
            f.write(patch_block)
            f.write("\n")
        f.write("}\n\n")
        f.write("// ************************************************************************* //\n")

    return target
