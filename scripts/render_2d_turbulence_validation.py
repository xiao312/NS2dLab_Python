from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from nslab2d.config import NS2dConfig
from nslab2d.diagnostics import curl, gather_timeseries
from nslab2d.solver import NS2dLabSolver


def central_diff_6th_periodic(f: np.ndarray, dt: float) -> np.ndarray:
    return (
        np.roll(f, -3)
        - 9.0 * np.roll(f, -2)
        + 45.0 * np.roll(f, -1)
        - 45.0 * np.roll(f, 1)
        + 9.0 * np.roll(f, 2)
        - np.roll(f, 3)
    ) / (60.0 * dt)


def main() -> None:
    outdir = Path("artifacts/ns2d_turbulence_256")
    outdir.mkdir(parents=True, exist_ok=True)

    cfg = NS2dConfig(N=256, dt=0.05, simutime_seconds=50.0, backend="cpu")
    solver = NS2dLabSolver(cfg)

    snapshot_steps = [0, 99, 249, 499, 749, 999]
    snapshots: list[tuple[int, np.ndarray]] = []

    for t in range(cfg.simutime_steps):
        solver.step()
        ekin, diss = gather_timeseries(
            solver.fields.U,
            solver.fields.V,
            solver.fields.KX,
            solver.fields.KY,
            solver.fields.dx,
            cfg.L,
            cfg.nu,
            solver.backend,
        )
        solver.timeseries.Ekin[t] = ekin
        solver.timeseries.Diss[t] = diss

        if t in snapshot_steps:
            w = curl(solver.fields.U, solver.fields.V, solver.fields.KX, solver.fields.KY, solver.backend)
            snapshots.append((t + 1, solver.backend.to_numpy(w)))

    solver.backend.synchronize()

    ekin = solver.backend.to_numpy(solver.timeseries.Ekin)
    diss = solver.backend.to_numpy(solver.timeseries.Diss)
    time = solver.backend.to_numpy(solver.timeseries.Time)

    d_ekin_dt = central_diff_6th_periodic(ekin, cfg.dt)
    minus_d_ekin_dt = -d_ekin_dt
    residual = np.abs(d_ekin_dt + diss)
    interior = slice(3, -3)
    residual_interior = residual[interior]

    np.save(outdir / "ekin.npy", ekin)
    np.save(outdir / "diss.npy", diss)
    np.save(outdir / "time.npy", time)
    np.save(outdir / "minus_d_ekin_dt.npy", minus_d_ekin_dt)
    np.save(outdir / "residual.npy", residual)
    np.save(outdir / "curl_final.npy", snapshots[-1][1])

    with open(outdir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"N = {cfg.N}\n")
        f.write(f"dt = {cfg.dt}\n")
        f.write(f"simutime_seconds = {cfg.simutime_seconds}\n")
        f.write(f"nu = {cfg.nu}\n")
        f.write(f"Ekin_min = {ekin.min():.16e}\n")
        f.write(f"Ekin_max = {ekin.max():.16e}\n")
        f.write(f"Diss_min = {diss.min():.16e}\n")
        f.write(f"Diss_max = {diss.max():.16e}\n")
        f.write(f"Residual_min = {residual.min():.16e}\n")
        f.write(f"Residual_max = {residual.max():.16e}\n")
        f.write(f"Residual_mean = {residual.mean():.16e}\n")
        f.write(f"Residual_median = {np.median(residual):.16e}\n")
        f.write(f"ResidualInterior_min = {residual_interior.min():.16e}\n")
        f.write(f"ResidualInterior_max = {residual_interior.max():.16e}\n")
        f.write(f"ResidualInterior_mean = {residual_interior.mean():.16e}\n")
        f.write(f"ResidualInterior_median = {np.median(residual_interior):.16e}\n")

    vmin = min(float(arr.min()) for _, arr in snapshots)
    vmax = max(float(arr.max()) for _, arr in snapshots)
    lim = max(abs(vmin), abs(vmax))

    plot_mask = (time >= 2.0) & (time <= 48.0)

    fig = plt.figure(figsize=(15, 10), constrained_layout=True)
    gs = fig.add_gridspec(3, 3)

    for idx, (step, arr) in enumerate(snapshots):
        ax = fig.add_subplot(gs[idx // 3, idx % 3])
        im = ax.imshow(arr, origin="lower", cmap="RdBu_r", vmin=-lim, vmax=lim)
        ax.set_title(f"curl(U,V), step={step}, t={step * cfg.dt:.2f}s")
        ax.set_xticks([])
        ax.set_yticks([])

    ax_energy = fig.add_subplot(gs[2, :])
    ax_energy.plot(time[plot_mask], minus_d_ekin_dt[plot_mask], label=r"$-dE_{kin}/dt$ (6th-order CD)", linewidth=1.5)
    ax_energy.plot(
        time[plot_mask],
        diss[plot_mask],
        label=r"$\chi(t)$",
        linewidth=1.0,
        marker="o",
        markersize=2.5,
        markevery=12,
    )
    ax_energy.set_xlabel("t")
    ax_energy.set_ylabel("value")
    ax_energy.set_title("Energy identity check for 2D pseudo-turbulence")
    ax_energy.grid(True, alpha=0.3)
    ax_energy.legend()

    cbar = fig.colorbar(im, ax=fig.axes[:-1], shrink=0.75)
    cbar.set_label("curl(U,V)")
    fig.suptitle("2D pseudo-turbulence: vorticity evolution and energy identity", fontsize=14)
    fig.savefig(outdir / "turbulence_montage_and_energy.png", dpi=220)
    plt.close(fig)

    plt.figure(figsize=(8, 4.8))
    plt.semilogy(time[plot_mask], residual[plot_mask], linewidth=1.4)
    plt.xlabel("t")
    plt.ylabel(r"$R = |dE_{kin}/dt + \chi|$")
    plt.title("Energy residual")
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(outdir / "energy_residual.png", dpi=220)
    plt.close()


if __name__ == "__main__":
    main()
