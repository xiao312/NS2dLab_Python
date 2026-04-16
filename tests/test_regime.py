from __future__ import annotations

from types import SimpleNamespace

from nslab2d.regime_diagram import compute_regime_point


def test_regime_point_uses_expected_formulae():
    hit = SimpleNamespace(
        uprime_component_rms=2.0,
        uprime_planar_rms=2.5,
        integral_length_scale_mean=0.01,
    )
    flame = SimpleNamespace(
        S_L=0.4,
        delta_alpha=0.0005,
        delta_T=0.0004,
    )
    point = compute_regime_point(hit, flame)
    assert point.uprime_over_Sl == 5.0
    assert point.lt_over_deltaL == 20.0
    assert abs(point.Da - 4.0) < 1e-12
    assert point.Ka > 0.0
