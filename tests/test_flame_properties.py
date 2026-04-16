from __future__ import annotations

import importlib.util

import pytest

from nslab2d.flame_properties import compute_laminar_flame_properties


pytestmark = pytest.mark.skipif(importlib.util.find_spec("cantera") is None, reason="Cantera unavailable")


def test_cantera_flame_properties_smoke():
    props = compute_laminar_flame_properties(
        mechanism="h2o2.yaml",
        fuel="H2",
        oxidizer="O2:1.0, AR:5.0",
        phi=1.0,
        T_u=300.0,
        P_u=101325.0,
        width=0.03,
        loglevel=0,
    )
    assert props.S_L > 0.0
    assert props.delta_alpha > 0.0
    assert props.delta_T > 0.0
    assert props.grid_points > 0
