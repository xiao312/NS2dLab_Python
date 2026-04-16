from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from nslab2d.compare import benchmark_backend, validate_manuscript_cases
from nslab2d.openfoam import write_openfoam_u_file
from nslab2d.plot_style import SIGNED_CMAP, add_light_ygrid, apply_academic_plot_style, categorical_colors


ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
DOCS_ASSETS = ROOT / "docs" / "assets" / "generated"
VALIDATION_DIR = DOCS_ASSETS / "validation"
BACKEND_DIR = DOCS_ASSETS / "backend"
FLAME_DIR = DOCS_ASSETS / "flame"
OPENFOAM_DIR = DOCS_ASSETS / "openfoam"


def _mkdirs() -> None:
    for path in [VALIDATION_DIR, BACKEND_DIR, FLAME_DIR, OPENFOAM_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _run(cmd: str) -> None:
    import subprocess

    subprocess.run(cmd, shell=True, check=True, cwd=ROOT)


def generate_validation_assets() -> None:
    _run(". ../.venv/bin/activate && python scripts/render_tg_vortex_validation.py")
    _run(". ../.venv/bin/activate && python scripts/render_default_ns2dlab_curl.py")
    _run(". ../.venv/bin/activate && python scripts/render_2d_turbulence_validation.py")

    _copy(ARTIFACTS / "ns2d_tg" / "tg_vectors_and_profile.png", VALIDATION_DIR / "taylor_green.png")
    _copy(ARTIFACTS / "ns2d_tg" / "summary.txt", VALIDATION_DIR / "taylor_green_summary.txt")
    _copy(ARTIFACTS / "ns2d_default" / "curl_montage.png", VALIDATION_DIR / "default_curl_montage.png")
    _copy(ARTIFACTS / "ns2d_default" / "curl_final.png", VALIDATION_DIR / "default_curl_final.png")
    _copy(ARTIFACTS / "ns2d_turbulence_256" / "turbulence_montage_and_energy.png", VALIDATION_DIR / "turbulence_energy.png")
    _copy(ARTIFACTS / "ns2d_turbulence_256" / "energy_residual.png", VALIDATION_DIR / "turbulence_residual.png")
    _copy(ARTIFACTS / "ns2d_turbulence_256" / "summary.txt", VALIDATION_DIR / "turbulence_summary.txt")


def generate_backend_assets() -> None:
    payload = validate_manuscript_cases()
    out_json = BACKEND_DIR / "manuscript_gpu_validation.json"
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    cpu = benchmark_backend("cpu", [64, 128, 256], [0.1, 0.1, 0.05], simutime_seconds=1.0, nu=1e-4)
    gpu = benchmark_backend("gpu", [64, 128, 256], [0.1, 0.1, 0.05], simutime_seconds=1.0, nu=1e-4)
    bench_payload = {
        "cpu": [asdict(entry) for entry in cpu],
        "gpu": [asdict(entry) for entry in gpu],
    }
    (BACKEND_DIR / "benchmark.json").write_text(json.dumps(bench_payload, indent=2, sort_keys=True), encoding="utf-8")

    apply_academic_plot_style()
    colors = categorical_colors(2)
    fig, ax = plt.subplots(figsize=(5.8, 3.8))
    N_cpu = [entry.N for entry in cpu]
    t_cpu = [entry.elapsed_time_seconds for entry in cpu]
    N_gpu = [entry.N for entry in gpu]
    t_gpu = [entry.elapsed_time_seconds for entry in gpu]
    ax.plot(N_cpu, t_cpu, marker="o", color=colors[0], label="CPU")
    ax.plot(N_gpu, t_gpu, marker="s", color=colors[1], label="GPU")
    ax.set_xlabel("Grid size N")
    ax.set_ylabel("Elapsed time (s)")
    ax.set_title("Short benchmark: CPU vs GPU")
    add_light_ygrid(ax)
    ax.legend()
    fig.savefig(BACKEND_DIR / "benchmark_runtime.png")
    plt.close(fig)

    cases = list(payload.keys())
    cpu_times = [payload[name]["cpu_elapsed_time_seconds"] for name in cases]
    gpu_times = [payload[name]["gpu_elapsed_time_seconds"] for name in cases]
    x = np.arange(len(cases))
    width = 0.36
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.bar(x - width / 2, cpu_times, width=width, color=colors[0], label="CPU")
    ax.bar(x + width / 2, gpu_times, width=width, color=colors[1], label="GPU")
    ax.set_xticks(x)
    ax.set_xticklabels(["Taylor–Green", "Default\nvortex array", "Pseudo-\nturbulence 256²"])
    ax.set_ylabel("Elapsed time (s)")
    ax.set_title("Manuscript-scale backend validation")
    add_light_ygrid(ax)
    ax.legend()
    fig.savefig(BACKEND_DIR / "manuscript_runtime.png")
    plt.close(fig)


def generate_flame_assets() -> None:
    _run(". ../.venv/bin/activate && python -m nslab2d.cli run --backend cpu --N 256 --dt 0.05 --simutime-seconds 50 --output artifacts/docs_case_256.mat --save-field-npz artifacts/docs_case_256_field.npz")
    _run(". ../.venv/bin/activate && python -m nslab2d.cli hit-stats --field-npz artifacts/docs_case_256_field.npz --output docs/assets/generated/flame/hit_stats.json")
    _run(". ../.venv/bin/activate && python -m nslab2d.cli flame-properties --mechanism h2o2.yaml --fuel H2 --oxidizer 'O2:1.0, AR:5.0' --phi 1.0 --Tu 300 --Pu 101325 --output docs/assets/generated/flame/flame_properties.json")
    _run(". ../.venv/bin/activate && python -m nslab2d.cli regime-diagram --field-npz artifacts/docs_case_256_field.npz --mechanism h2o2.yaml --fuel H2 --oxidizer 'O2:1.0, AR:5.0' --phi 1.0 --Tu 300 --Pu 101325 --output docs/assets/generated/flame/regime_diagram.png --json-output docs/assets/generated/flame/regime_diagram.json --annotate '2D HIT case'")

    write_openfoam_u_file(
        np.load(ARTIFACTS / "docs_case_256_field.npz")["U"],
        np.load(ARTIFACTS / "docs_case_256_field.npz")["V"],
        case_dir=OPENFOAM_DIR / "example_case",
        time_dir="0",
        ordering="x-fastest",
    )

    ufile = OPENFOAM_DIR / "example_case" / "0" / "U"
    lines = ufile.read_text(encoding="utf-8").splitlines()
    snippet = "\n".join(lines[:26]) + "\n..."
    (OPENFOAM_DIR / "U_snippet.txt").write_text(snippet, encoding="utf-8")


def main() -> None:
    _mkdirs()
    generate_validation_assets()
    generate_backend_assets()
    generate_flame_assets()


if __name__ == "__main__":
    main()
