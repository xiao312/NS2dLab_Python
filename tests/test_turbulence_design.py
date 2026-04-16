from __future__ import annotations

import numpy as np

from nslab2d.config import NS2dConfig
from pathlib import Path

from nslab2d.turbulence_design import (
    compute_regime_targets,
    generate_divergence_free_spectral_field,
    plot_tuning_search,
    rescale_field_to_target_uprime,
    save_tuning_artifacts,
    tune_field_to_regime_targets,
)


def test_compute_regime_targets_returns_expected_values():
    targets = compute_regime_targets(S_L=0.4, delta_L=5e-4, lt_over_deltaL=20.0, uprime_over_Sl=5.0)
    assert np.isclose(targets.target_integral_length_scale, 0.01)
    assert np.isclose(targets.target_uprime, 2.0)


def test_rescaling_hits_target_uprime():
    x = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    X, Y = np.meshgrid(x, x)
    U = np.sin(X)
    V = np.cos(Y)
    U2, V2, stats, alpha = rescale_field_to_target_uprime(U, V, dx=x[1] - x[0], dy=x[1] - x[0], target_uprime=0.25)
    assert alpha > 0.0
    assert np.isclose(stats.uprime_component_rms, 0.25, rtol=1e-12)
    assert U2.shape == U.shape
    assert V2.shape == V.shape


def test_spectral_initializer_generates_nontrivial_field():
    cfg = NS2dConfig(N=32, dt=0.1, simutime_seconds=1.0)
    U, V, dx, dy = generate_divergence_free_spectral_field(cfg, k0=4.0, bandwidth=1.0, seed=3)
    U = np.asarray(U)
    V = np.asarray(V)
    assert U.shape == (32, 32)
    assert V.shape == (32, 32)
    assert dx > 0.0 and dy > 0.0
    assert np.std(U) > 0.0
    assert np.std(V) > 0.0


def test_tuning_search_returns_history_and_plot(tmp_path: Path):
    targets = compute_regime_targets(S_L=0.4, delta_L=5e-4, lt_over_deltaL=20.0, uprime_over_Sl=5.0)
    result = tune_field_to_regime_targets(
        targets,
        N=32,
        N_values=[32, 64],
        L_values=[2 * np.pi, 4 * np.pi],
        mode_values=[2.0, 4.0],
        evolve_seconds=0.0,
        keep_top_candidates=4,
    )
    assert len(result.history) == 8
    assert result.best_mode_index in {2.0, 4.0}
    assert result.best_N in {32, 64}
    assert len(result.top_candidates) <= 4
    plot_path = tmp_path / 'search.png'
    plot_tuning_search(result, output_path=plot_path)
    assert plot_path.exists()

    artifacts = save_tuning_artifacts(result, output_dir=tmp_path / 'artifacts', top_n=3)
    assert Path(artifacts['final_curl']).exists()
    assert Path(artifacts['history_curl_montage']).exists()
    assert Path(artifacts['regime_diagram_history']).exists()
