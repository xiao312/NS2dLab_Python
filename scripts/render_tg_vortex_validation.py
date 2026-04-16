from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from nslab2d.config import NS2dConfig
from nslab2d.diagnostics import divergence
from nslab2d.solver import NS2dLabSolver


def tg_exact(x, y, t, nu):
    decay = np.exp(-nu * t)
    u = np.sin(x) * np.cos(y) * decay
    v = -np.cos(x) * np.sin(y) * decay
    p = 0.25 * (np.cos(2 * x) + np.cos(2 * y)) * np.exp(-2 * nu * t)
    return u, v, p


def main() -> None:
    outdir = Path("artifacts/ns2d_tg")
    outdir.mkdir(parents=True, exist_ok=True)

    final_time = 1.0
    cfg = NS2dConfig(N=32, dt=0.1, simutime_seconds=final_time, nu=1e-4, backend="cpu")
    solver = NS2dLabSolver(cfg)

    X = solver.backend.to_numpy(solver.fields.X)
    Y = solver.backend.to_numpy(solver.fields.Y)
    U0, V0, _ = tg_exact(X, Y, 0.0, cfg.nu)
    solver.fields.U = solver.backend.asarray(U0, dtype=solver.backend.xp.float64)
    solver.fields.V = solver.backend.asarray(V0, dtype=solver.backend.xp.float64)

    result = solver.run()

    U_num = result.backend.to_numpy(result.fields.U)
    V_num = result.backend.to_numpy(result.fields.V)
    U_ex, V_ex, _ = tg_exact(X, Y, final_time, cfg.nu)

    div = result.backend.to_numpy(divergence(result.fields.U, result.fields.V, result.fields.KX, result.fields.KY, result.backend))
    max_div = float(np.max(np.abs(div)))
    u_err = U_num - U_ex
    v_err = V_num - V_ex

    # profile along y=0, as requested x on x-axis and U/Umax on y-axis
    profile_idx = 0
    xline = X[profile_idx, :]
    u_num_line = U_num[profile_idx, :]
    u_ex_line = U_ex[profile_idx, :]
    umax = float(np.max(np.abs(u_ex_line)))

    stride = 2
    plt.figure(figsize=(13, 5))

    ax1 = plt.subplot(1, 2, 1)
    ax1.quiver(
        X[::stride, ::stride],
        Y[::stride, ::stride],
        U_num[::stride, ::stride],
        V_num[::stride, ::stride],
        color="tab:blue",
        angles="xy",
        scale_units="xy",
        scale=1.8,
        width=0.004,
    )
    ax1.set_title(f"TG vortex velocity vectors, t={final_time:.1f} s")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_xlim(float(X.min()), float(X.max()))
    ax1.set_ylim(float(Y.min()), float(Y.max()))
    ax1.set_aspect("equal")

    ax2 = plt.subplot(1, 2, 2)
    ax2.plot(xline, u_num_line / umax, "o-", label="NS2dLab Python", markersize=4)
    ax2.plot(xline, u_ex_line / umax, "k--", label="Analytical", linewidth=1.5)
    ax2.set_xlabel("x")
    ax2.set_ylabel("U/Umax")
    ax2.set_title("Velocity profile at y=0")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.suptitle(
        "2D Taylor-Green vortex validation\n"
        f"N={cfg.N}, dt={cfg.dt}, nu={cfg.nu}, max|div u|={max_div:.3e}",
        y=1.02,
    )
    plt.tight_layout()
    plt.savefig(outdir / "tg_vectors_and_profile.png", dpi=220, bbox_inches="tight")
    plt.close()

    np.save(outdir / "U_num.npy", U_num)
    np.save(outdir / "V_num.npy", V_num)
    np.save(outdir / "U_exact.npy", U_ex)
    np.save(outdir / "V_exact.npy", V_ex)
    np.save(outdir / "xline.npy", xline)
    np.save(outdir / "u_num_line.npy", u_num_line)
    np.save(outdir / "u_exact_line.npy", u_ex_line)

    with open(outdir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"final_time = {final_time}\n")
        f.write(f"N = {cfg.N}\n")
        f.write(f"dt = {cfg.dt}\n")
        f.write(f"nu = {cfg.nu}\n")
        f.write(f"max_abs_divergence = {max_div:.16e}\n")
        f.write(f"u_linf_error = {np.max(np.abs(u_err)):.16e}\n")
        f.write(f"v_linf_error = {np.max(np.abs(v_err)):.16e}\n")
        f.write(f"u_l2_error = {np.sqrt(np.mean(u_err**2)):.16e}\n")
        f.write(f"v_l2_error = {np.sqrt(np.mean(v_err**2)):.16e}\n")


if __name__ == "__main__":
    main()
