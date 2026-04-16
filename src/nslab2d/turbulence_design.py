"""Inverse-design helpers for turbulence fields used in regime-diagram targeting.

This module provides a practical workflow for constructing 2D divergence-free fields
with approximately prescribed turbulence intensity and integral length scale.

The workflow is intentionally pragmatic:

1. compute target `u'` and `l_t` from a desired regime-diagram point
2. generate a divergence-free random field with a tunable spectral peak `k0`
3. rescale the field amplitude to hit the target `u'`
4. optionally evolve the field and select the time/sample closest to the target pair

The resulting field will generally not hit the target exactly on the first try, but it
is usually close enough for engineering use and can be improved with a small search over
`k0` and evolution time.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import pi
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .backend import Backend, make_backend
from .config import NS2dConfig
from .diagnostics import curl
from .field_io import save_velocity_field_npz
from .hit_stats import HITStats, compute_hit_stats
from .plot_style import SIGNED_CMAP, add_light_ygrid, apply_academic_plot_style, categorical_colors
from .projection import project
from .solver import NS2dLabSolver


@dataclass(slots=True)
class RegimeTargets:
    """Target turbulence quantities derived from a regime-diagram location."""

    S_L: float
    delta_L: float
    lt_over_deltaL: float
    uprime_over_Sl: float
    target_integral_length_scale: float
    target_uprime: float


@dataclass(slots=True)
class CandidateResult:
    """One candidate field evaluation during the tuning/search process."""

    N: int
    L: float
    dx: float
    dy: float
    k0: float
    mode_index: float | None
    sample_time: float
    score: float
    stats: HITStats
    U: np.ndarray
    V: np.ndarray


@dataclass(slots=True)
class CandidateSummary:
    """Compact, JSON-friendly summary of one evaluated candidate."""

    N: int
    L: float
    dx: float
    k0: float
    mode_index: float | None
    sample_time: float
    score: float
    uprime: float
    uprime_over_Sl: float
    integral_length_scale: float
    lt_over_deltaL: float
    lt_over_dx: float
    lt_over_L: float


@dataclass(slots=True)
class TunedFieldResult:
    """Final selected field and summary metadata."""

    targets: RegimeTargets
    best_N: int
    best_L: float
    best_dx: float
    best_dy: float
    best_k0: float
    best_mode_index: float | None
    best_sample_time: float
    best_score: float
    stats: HITStats
    U: np.ndarray
    V: np.ndarray
    history: list[CandidateSummary]
    top_candidates: list[CandidateResult]


def compute_regime_targets(S_L: float, delta_L: float, lt_over_deltaL: float, uprime_over_Sl: float) -> RegimeTargets:
    """Convert a desired regime-diagram location into target turbulence values."""
    return RegimeTargets(
        S_L=float(S_L),
        delta_L=float(delta_L),
        lt_over_deltaL=float(lt_over_deltaL),
        uprime_over_Sl=float(uprime_over_Sl),
        target_integral_length_scale=float(lt_over_deltaL * delta_L),
        target_uprime=float(uprime_over_Sl * S_L),
    )


def _k_magnitude(KX, KY, xp):
    return xp.sqrt(KX**2 + KY**2)


def generate_divergence_free_spectral_field(
    config: NS2dConfig,
    *,
    backend: Backend | None = None,
    k0: float = 6.0,
    bandwidth: float = 1.5,
    seed: int = 0,
) -> tuple[Any, Any, float, float]:
    """Generate a random divergence-free velocity field with a tunable spectral peak.

    The field is built from a random streamfunction in Fourier space whose amplitude is
    concentrated around the chosen peak wavenumber `k0`. Velocities are then derived as

    - `U_hat = i * KY * psi_hat`
    - `V_hat = -i * KX * psi_hat`

    which guarantees incompressibility analytically before a final projection clean-up.
    """
    backend = backend or make_backend(config.backend, fftw_threads=config.fftw_threads, fftw_cache_enable=config.fftw_cache_enable)
    xp = backend.xp
    N = config.N
    dx = config.L / N

    kx1 = xp.mod(0.5 + xp.arange(N, dtype=xp.float64) / N, 1.0) - 0.5
    ky1 = xp.mod(0.5 + xp.arange(N, dtype=xp.float64) / N, 1.0) - 0.5
    kx = kx1 * (2 * pi / dx)
    ky = ky1 * (2 * pi / dx)
    KX, KY = xp.meshgrid(kx, ky)
    AA = ((xp.abs(KX) < (2.0 / 3.0) * xp.max(kx)) * (xp.abs(KY) < (2.0 / 3.0) * xp.max(ky))).astype(xp.float64)
    kmag = _k_magnitude(KX, KY, xp)

    rng = np.random.default_rng(seed)
    phase = rng.uniform(0.0, 2.0 * np.pi, size=(N, N))
    amplitude = np.exp(-0.5 * ((backend.to_numpy(kmag) - k0) / max(bandwidth, 1e-6)) ** 2)
    amplitude[0, 0] = 0.0
    amplitude = backend.asarray(amplitude, dtype=xp.float64)
    phase = backend.asarray(phase, dtype=xp.float64)

    psi_hat = amplitude * xp.exp(1j * phase)
    psi_hat = AA * psi_hat
    U_hat = 1j * KY * psi_hat
    V_hat = -1j * KX * psi_hat
    U = backend.real(backend.ifft2(U_hat))
    V = backend.real(backend.ifft2(V_hat))
    U, V = project(U, V, KX, KY, AA, backend)
    return U, V, dx, dx


def rescale_field_to_target_uprime(U: np.ndarray, V: np.ndarray, dx: float, dy: float, target_uprime: float) -> tuple[np.ndarray, np.ndarray, HITStats, float]:
    """Rescale a field amplitude so its component RMS matches the target `u'`."""
    stats = compute_hit_stats(U, V, dx, dy)
    if np.isclose(stats.uprime_component_rms, 0.0):
        raise ValueError("Cannot rescale a field with zero measured uprime")
    alpha = float(target_uprime / stats.uprime_component_rms)
    U2 = alpha * U
    V2 = alpha * V
    stats2 = compute_hit_stats(U2, V2, dx, dy)
    return U2, V2, stats2, alpha


def _candidate_score(stats: HITStats, targets: RegimeTargets) -> float:
    rel_u = (stats.uprime_component_rms - targets.target_uprime) / max(targets.target_uprime, 1e-16)
    rel_l = (stats.integral_length_scale_mean - targets.target_integral_length_scale) / max(targets.target_integral_length_scale, 1e-16)
    return float(rel_u**2 + rel_l**2)


def _candidate_summary_from_stats(
    stats: HITStats,
    N: int,
    L: float,
    dx: float,
    k0: float,
    mode_index: float | None,
    sample_time: float,
    score: float,
    targets: RegimeTargets,
) -> CandidateSummary:
    return CandidateSummary(
        N=int(N),
        L=float(L),
        dx=float(dx),
        k0=float(k0),
        mode_index=None if mode_index is None else float(mode_index),
        sample_time=float(sample_time),
        score=float(score),
        uprime=float(stats.uprime_component_rms),
        uprime_over_Sl=float(stats.uprime_component_rms / max(targets.S_L, 1e-16)),
        integral_length_scale=float(stats.integral_length_scale_mean),
        lt_over_deltaL=float(stats.integral_length_scale_mean / max(targets.delta_L, 1e-16)),
        lt_over_dx=float(stats.integral_length_scale_mean / max(dx, 1e-16)),
        lt_over_L=float(stats.integral_length_scale_mean / max(L, 1e-16)),
    )


def _evaluate_field(
    U: np.ndarray,
    V: np.ndarray,
    dx: float,
    dy: float,
    N: int,
    L: float,
    k0: float,
    mode_index: float | None,
    sample_time: float,
    targets: RegimeTargets,
) -> CandidateResult:
    stats = compute_hit_stats(U, V, dx, dy)
    return CandidateResult(
        N=int(N),
        L=float(L),
        dx=float(dx),
        dy=float(dy),
        k0=float(k0),
        mode_index=None if mode_index is None else float(mode_index),
        sample_time=float(sample_time),
        score=_candidate_score(stats, targets),
        stats=stats,
        U=np.asarray(U, dtype=np.float64),
        V=np.asarray(V, dtype=np.float64),
    )


def _update_top_candidates(top_candidates: list[CandidateResult], candidate: CandidateResult, keep_top_candidates: int) -> None:
    top_candidates.append(candidate)
    top_candidates.sort(key=lambda entry: entry.score)
    del top_candidates[keep_top_candidates:]


def tune_field_to_regime_targets(
    targets: RegimeTargets,
    *,
    N: int = 128,
    nu: float = 1e-4,
    L: float = 2 * pi,
    backend_name: str = "cpu",
    N_values: list[int] | None = None,
    L_values: list[float] | None = None,
    k0_values: list[float] | None = None,
    mode_values: list[float] | None = None,
    bandwidth: float = 1.5,
    bandwidth_modes: float = 1.5,
    seed: int = 0,
    evolve_seconds: float = 0.0,
    dt: float = 0.05,
    sample_every: int = 1,
    keep_top_candidates: int = 8,
) -> TunedFieldResult:
    """Search for a field whose measured `u'` and `l_t` are close to the target pair."""
    if N_values is None:
        N_values = [N]
    if L_values is None:
        L_values = [L]
    if k0_values is None:
        k0_values = [2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 16.0]

    best: CandidateResult | None = None
    history: list[CandidateSummary] = []
    top_candidates: list[CandidateResult] = []
    combo_index = 0
    for N_current in N_values:
        for L_current in L_values:
            base_cfg = NS2dConfig(N=N_current, dt=dt, simutime_seconds=max(evolve_seconds, dt), nu=nu, L=L_current, backend=backend_name)
            backend = make_backend(base_cfg.backend, fftw_threads=base_cfg.fftw_threads, fftw_cache_enable=base_cfg.fftw_cache_enable)
            k_base = 2.0 * pi / L_current
            search_pairs = (
                [(float(mode), float(mode) * k_base, float(bandwidth_modes) * k_base) for mode in mode_values]
                if mode_values is not None
                else [(None, float(k0), float(bandwidth)) for k0 in k0_values]
            )
            for idx, (mode_index, k0, bandwidth_current) in enumerate(search_pairs):
                U_backend, V_backend, dx, dy = generate_divergence_free_spectral_field(
                    base_cfg,
                    backend=backend,
                    k0=k0,
                    bandwidth=bandwidth_current,
                    seed=seed + combo_index + idx,
                )
                U = backend.to_numpy(U_backend)
                V = backend.to_numpy(V_backend)
                if np.isclose(np.std(U), 0.0) and np.isclose(np.std(V), 0.0):
                    continue
                U, V, _, _ = rescale_field_to_target_uprime(U, V, dx, dy, targets.target_uprime)
                candidate = _evaluate_field(U, V, dx, dy, N_current, L_current, k0, mode_index, 0.0, targets)
                history.append(_candidate_summary_from_stats(candidate.stats, N_current, L_current, dx, k0, mode_index, 0.0, candidate.score, targets))
                _update_top_candidates(top_candidates, candidate, keep_top_candidates)
                if best is None or candidate.score < best.score:
                    best = candidate

                if evolve_seconds > 0.0:
                    evolve_cfg = NS2dConfig(N=N_current, dt=dt, simutime_seconds=evolve_seconds, nu=nu, L=L_current, backend=backend_name)
                    solver = NS2dLabSolver(evolve_cfg)
                    solver.fields.U = solver.backend.asarray(U, dtype=solver.backend.xp.float64)
                    solver.fields.V = solver.backend.asarray(V, dtype=solver.backend.xp.float64)
                    for step in range(evolve_cfg.simutime_steps):
                        solver.step()
                        if step % sample_every != 0 and step != evolve_cfg.simutime_steps - 1:
                            continue
                        U_s = solver.backend.to_numpy(solver.fields.U)
                        V_s = solver.backend.to_numpy(solver.fields.V)
                        sample_time = (step + 1) * evolve_cfg.dt
                        candidate = _evaluate_field(U_s, V_s, solver.fields.dx, solver.fields.dx, N_current, L_current, k0, mode_index, sample_time, targets)
                        history.append(_candidate_summary_from_stats(candidate.stats, N_current, L_current, solver.fields.dx, k0, mode_index, sample_time, candidate.score, targets))
                        _update_top_candidates(top_candidates, candidate, keep_top_candidates)
                        if best is None or candidate.score < best.score:
                            best = candidate
            combo_index += 1000

    assert best is not None
    return TunedFieldResult(
        targets=targets,
        best_N=best.N,
        best_L=best.L,
        best_dx=best.dx,
        best_dy=best.dy,
        best_k0=best.k0,
        best_mode_index=best.mode_index,
        best_sample_time=best.sample_time,
        best_score=best.score,
        stats=best.stats,
        U=best.U,
        V=best.V,
        history=history,
        top_candidates=top_candidates,
    )


def tuned_field_result_to_dict(result: TunedFieldResult) -> dict[str, Any]:
    """Convert a tuned-field result to JSON-serializable metadata."""
    return {
        "targets": asdict(result.targets),
        "best_N": result.best_N,
        "best_L": result.best_L,
        "best_dx": result.best_dx,
        "best_dy": result.best_dy,
        "best_k0": result.best_k0,
        "best_mode_index": result.best_mode_index,
        "best_sample_time": result.best_sample_time,
        "best_score": result.best_score,
        "stats": asdict(result.stats),
        "history": [asdict(entry) for entry in result.history],
    }


def save_tuned_field(path: str | Path, result: TunedFieldResult, dx: float, dy: float | None = None) -> None:
    """Save a tuned field using the standard velocity-field snapshot format."""
    metadata = tuned_field_result_to_dict(result)
    save_velocity_field_npz(path, U=result.U, V=result.V, dx=dx, dy=dy or dx, metadata=metadata)


def plot_tuning_search(result: TunedFieldResult, *, output_path: str | Path, title: str = "Tuning search in regime space") -> None:
    """Plot all tested candidates in regime space and highlight the best one."""
    apply_academic_plot_style()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    colors = categorical_colors(3)
    x_hist = np.array([entry.lt_over_deltaL for entry in result.history], dtype=float)
    y_hist = np.array([entry.uprime_over_Sl for entry in result.history], dtype=float)
    scores = np.array([entry.score for entry in result.history], dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    sc = ax.scatter(x_hist, y_hist, c=scores, cmap="cividis_r", s=42, alpha=0.85)
    ax.scatter(
        [result.targets.lt_over_deltaL],
        [result.targets.uprime_over_Sl],
        marker="x",
        s=150,
        linewidths=2.0,
        color=colors[1],
        zorder=5,
    )
    achieved_x = result.stats.integral_length_scale_mean / result.targets.delta_L
    achieved_y = result.stats.uprime_component_rms / result.targets.S_L
    ax.scatter(
        [achieved_x],
        [achieved_y],
        s=130,
        color=colors[0],
        edgecolors="white",
        linewidths=0.8,
        zorder=6,
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$l_t / \delta_L$")
    ax.set_ylabel(r"$u' / S_L$")
    ax.set_title(title)
    add_light_ygrid(ax)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("score")
    ax.annotate("target", (result.targets.lt_over_deltaL, result.targets.uprime_over_Sl), xytext=(6, 6), textcoords="offset points")
    ax.annotate("achieved", (achieved_x, achieved_y), xytext=(6, -10), textcoords="offset points")
    mode_text = "" if result.best_mode_index is None else f", m={result.best_mode_index:.3g}"
    fig.text(0.01, 0.01, f"Best: N={result.best_N}, L={result.best_L:.4g}, k0={result.best_k0:.3g}{mode_text}, t={result.best_sample_time:.3g} s")
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)


def _wavenumber_grids(N: int, dx: float) -> tuple[np.ndarray, np.ndarray]:
    kx1 = np.mod(0.5 + np.arange(N, dtype=np.float64) / N, 1.0) - 0.5
    ky1 = np.mod(0.5 + np.arange(N, dtype=np.float64) / N, 1.0) - 0.5
    kx = kx1 * (2 * pi / dx)
    ky = ky1 * (2 * pi / dx)
    return np.meshgrid(kx, ky)


def compute_curl_field(U: np.ndarray, V: np.ndarray, dx: float) -> np.ndarray:
    """Compute curl/vorticity for a saved or tuned 2D velocity field."""
    backend = make_backend("cpu")
    KX, KY = _wavenumber_grids(U.shape[0], dx)
    return np.asarray(curl(U, V, KX, KY, backend), dtype=np.float64)


def plot_final_curl(result: TunedFieldResult, *, output_path: str | Path, title: str | None = None) -> None:
    """Save a curl plot for the final selected field."""
    apply_academic_plot_style()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    field = compute_curl_field(result.U, result.V, result.best_dx)
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    im = ax.imshow(field, origin="lower", cmap=SIGNED_CMAP)
    ax.set_xticks([])
    ax.set_yticks([])
    if title is None:
        title = (
            f"Final curl: N={result.best_N}, L={result.best_L:.4g}, "
            f"$l_t/\\delta_L$={result.stats.integral_length_scale_mean / result.targets.delta_L:.3f}, "
            f"$u'/S_L$={result.stats.uprime_component_rms / result.targets.S_L:.3f}"
        )
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label="curl(U,V)")
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)


def plot_history_curl_montage(
    result: TunedFieldResult,
    *,
    output_path: str | Path,
    top_n: int = 8,
    title: str = "Top tuning-history curl montage",
) -> None:
    """Save a montage of the best-scoring candidates' curl fields."""
    apply_academic_plot_style()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    ranked = sorted(result.top_candidates, key=lambda entry: entry.score)[:top_n]
    if not ranked:
        raise ValueError("No stored top candidates available for curl montage")

    arrays: list[np.ndarray] = []
    lim = 0.0
    for entry in ranked:
        arr = compute_curl_field(entry.U, entry.V, entry.dx)
        arrays.append(arr)
        lim = max(lim, float(np.max(np.abs(arr))))

    ncols = 4
    nrows = int(np.ceil(len(ranked) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.6 * ncols, 3.2 * nrows), constrained_layout=True)
    axes_flat = np.atleast_1d(axes).ravel()
    im = None
    for ax, arr, entry, rank in zip(axes_flat, arrays, ranked, range(1, len(ranked) + 1)):
        im = ax.imshow(arr, origin="lower", cmap=SIGNED_CMAP, vmin=-lim, vmax=lim)
        ax.set_xticks([])
        ax.set_yticks([])
        mode_text = "" if entry.mode_index is None else f", m={entry.mode_index:.3g}"
        ax.set_title(
            f"#{rank}: N={entry.N}, L={entry.L:.3g}{mode_text}\n"
            f"$l_t/\\delta_L$={entry.stats.integral_length_scale_mean / result.targets.delta_L:.3f}, score={entry.score:.3g}"
        )
    for ax in axes_flat[len(ranked):]:
        ax.axis("off")
    if im is not None:
        fig.colorbar(im, ax=axes_flat.tolist(), shrink=0.82, label="curl(U,V)")
    fig.suptitle(title)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def plot_regime_diagram_with_history(
    result: TunedFieldResult,
    *,
    output_path: str | Path,
    title: str = "Regime diagram with target, achieved point, and search history",
    top_n: int = 8,
) -> None:
    """Save a Borghi/Peters-style diagram with search-history markers."""
    apply_academic_plot_style()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    x_full = np.logspace(-1, 4, 600)
    x_turb = np.logspace(0, 4, 500)
    re_t_1 = x_full ** -1.0
    uprime_sl_1 = np.ones_like(x_turb)
    da_1 = x_turb
    ka_1 = x_turb ** (1.0 / 3.0)
    ka_100 = 100.0 ** (2.0 / 3.0) * x_full ** (1.0 / 3.0)

    colors = categorical_colors(6)
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    ax.loglog(x_full, re_t_1, "-", linewidth=1.1, color=colors[0])
    ax.loglog(x_turb, uprime_sl_1, "-", linewidth=1.1, color=colors[1])
    ax.loglog(x_turb, da_1, "--", linewidth=1.1, color=colors[2])
    ax.loglog(x_turb, ka_1, linestyle="-.", linewidth=1.1, color=colors[3])
    ax.loglog(x_full, ka_100, linestyle=":", linewidth=1.4, color=colors[4])

    x_hist = np.array([entry.lt_over_deltaL for entry in result.history], dtype=float)
    y_hist = np.array([entry.uprime_over_Sl for entry in result.history], dtype=float)
    ax.scatter(x_hist, y_hist, s=18, alpha=0.20, color=colors[5], zorder=4)
    top = sorted(result.history, key=lambda entry: entry.score)[:top_n]
    ax.scatter(
        [entry.lt_over_deltaL for entry in top],
        [entry.uprime_over_Sl for entry in top],
        s=52,
        alpha=0.78,
        color=colors[0],
        edgecolors="white",
        linewidths=0.5,
        zorder=5,
    )

    achieved_x = result.stats.integral_length_scale_mean / result.targets.delta_L
    achieved_y = result.stats.uprime_component_rms / result.targets.S_L
    ax.scatter([result.targets.lt_over_deltaL], [result.targets.uprime_over_Sl], marker="x", s=180, linewidths=2.2, color="#b22222", zorder=7)
    ax.scatter([achieved_x], [achieved_y], s=180, color="#202020", edgecolors="white", linewidths=0.9, zorder=8)
    ax.annotate("target", (result.targets.lt_over_deltaL, result.targets.uprime_over_Sl), xytext=(8, 8), textcoords="offset points")
    ax.annotate("best achieved", (achieved_x, achieved_y), xytext=(8, -12), textcoords="offset points")

    ax.text(0.10, 0.11, "Laminar / weakly perturbed", transform=ax.transAxes)
    ax.text(0.29, 0.28, "Wrinkled flamelets", transform=ax.transAxes)
    ax.text(0.28, 0.47, "Corrugated flamelets", transform=ax.transAxes)
    ax.text(0.60, 0.67, "Thin reaction zones", transform=ax.transAxes)
    ax.text(0.73, 0.83, "Broken reaction zones", transform=ax.transAxes)
    ax.text(2.0e-1, 7.0, r"$Re_t=(u'/S_L)(l_t/\delta_L)=1$", color=colors[0], rotation=-27)
    ax.text(2.4, 1.18, r"$u'/S_L=1$", color=colors[1], rotation=0)
    ax.text(2.5e1, 3.0e1, r"$D_a=1$", color=colors[2], rotation=27)
    ax.text(1.7, 2.2, r"$K_a=1$", color=colors[3], rotation=18)
    ax.text(8.0, 3.5e1, r"$K_a=100$", color=colors[4], rotation=18)

    ax.set_xlabel(r"$l_t / \delta_L$")
    ax.set_ylabel(r"$u' / S_L$")
    ax.set_title(title)
    add_light_ygrid(ax)
    ax.grid(True, which="major", axis="x", alpha=0.15)
    ax.set_xlim(1e-1, 1e4)
    ax.set_ylim(1e-2, 1e3)
    mode_text = "" if result.best_mode_index is None else f", m={result.best_mode_index:.3g}"
    fig.text(
        0.01,
        0.01,
        f"Best: N={result.best_N}, L={result.best_L:.4g}, k0={result.best_k0:.3g}{mode_text}, "
        f"u'/S_L={achieved_y:.3g}, l_t/delta_L={achieved_x:.3g}",
    )
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)


def save_tuning_artifacts(result: TunedFieldResult, *, output_dir: str | Path, top_n: int = 8) -> dict[str, str]:
    """Save reusable visualization artifacts for a tuned field search."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    final_curl = output / "final_curl.png"
    curl_montage = output / "history_curl_montage.png"
    regime_plot = output / "regime_diagram_history.png"
    plot_final_curl(result, output_path=final_curl)
    plot_history_curl_montage(result, output_path=curl_montage, top_n=top_n)
    plot_regime_diagram_with_history(result, output_path=regime_plot, top_n=top_n)
    return {
        "final_curl": str(final_curl),
        "history_curl_montage": str(curl_montage),
        "regime_diagram_history": str(regime_plot),
    }
