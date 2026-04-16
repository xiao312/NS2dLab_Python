from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from nslab2d.config import NS2dConfig
from nslab2d.diagnostics import curl, gather_timeseries
from nslab2d.plot_style import SIGNED_CMAP, apply_academic_plot_style
from nslab2d.solver import NS2dLabSolver


def main() -> None:
    apply_academic_plot_style()
    outdir = Path("artifacts/ns2d_default")
    outdir.mkdir(parents=True, exist_ok=True)

    cfg = NS2dConfig(N=128, dt=0.1, simutime_seconds=50.0, backend="cpu")
    solver = NS2dLabSolver(cfg)

    snapshot_steps = [0, 49, 99, 199, 299, 399, 499]
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
            c = curl(solver.fields.U, solver.fields.V, solver.fields.KX, solver.fields.KY, solver.backend)
            snapshots.append((t + 1, solver.backend.to_numpy(c)))

    solver.backend.synchronize()

    np.save(outdir / "ekin.npy", solver.backend.to_numpy(solver.timeseries.Ekin))
    np.save(outdir / "diss.npy", solver.backend.to_numpy(solver.timeseries.Diss))
    np.save(outdir / "time.npy", solver.backend.to_numpy(solver.timeseries.Time))
    np.save(outdir / "curl_final.npy", snapshots[-1][1])

    vmin = min(float(arr.min()) for _, arr in snapshots)
    vmax = max(float(arr.max()) for _, arr in snapshots)
    lim = max(abs(vmin), abs(vmax))

    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    axes = axes.ravel()
    im = None
    for ax, (step, arr) in zip(axes, snapshots):
        im = ax.imshow(arr, origin="lower", cmap=SIGNED_CMAP, vmin=-lim, vmax=lim)
        ax.set_title(f"step={step}, t={step * cfg.dt:.1f}s")
        ax.set_xticks([])
        ax.set_yticks([])
    for ax in axes[len(snapshots):]:
        ax.axis("off")
    if im is not None:
        cbar = fig.colorbar(im, ax=axes.tolist(), shrink=0.8)
        cbar.set_label("curl(U,V)")
    fig.suptitle("NS2dLab default case: curl of velocity snapshots")
    fig.savefig(outdir / "curl_montage.png", dpi=180)
    plt.close(fig)

    step, arr = snapshots[-1]
    arr_min = float(arr.min())
    arr_max = float(arr.max())
    plt.figure(figsize=(6.5, 6))
    plt.imshow(arr, origin="lower", cmap=SIGNED_CMAP, vmin=arr_min, vmax=arr_max)
    plt.xticks([])
    plt.yticks([])
    plt.title(f"NS2dLab default curl, final frame step={step}, t={step * cfg.dt:.1f}s")
    plt.colorbar(label="curl(U,V)")
    plt.tight_layout()
    plt.savefig(outdir / "curl_final.png", dpi=200)
    plt.close()


if __name__ == "__main__":
    main()
