from __future__ import annotations

import numpy as np

from nslab2d.hit_stats import compute_hit_stats


def test_hit_stats_for_simple_sinusoidal_field():
    n = 64
    L = 2 * np.pi
    dx = L / n
    x = np.arange(n) * dx
    y = np.arange(n) * dx
    X, Y = np.meshgrid(x, y)
    U = np.sin(X)
    V = np.cos(Y)

    stats = compute_hit_stats(U, V, dx)
    assert abs(stats.mean_u) < 1e-12
    assert abs(stats.mean_v) < 1e-12
    assert np.isclose(stats.uprime_component_rms, np.sqrt(0.5), atol=2e-2)
    assert stats.integral_length_scale_x > 0
    assert stats.integral_length_scale_y > 0
