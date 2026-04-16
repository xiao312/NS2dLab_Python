"""Command-line interface for NS2dLab."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .backend import get_gpu_info, gpu_is_available
from .compare import benchmark_backend, compare_cpu_gpu, validate_manuscript_cases
from .config import NS2dConfig
from .field_io import load_velocity_field_npz, save_velocity_field_npz
from .flame_properties import compute_laminar_flame_properties, flame_properties_to_dict
from .hit_stats import compute_hit_stats
from .io import compare_mat_timeseries, save_timeseries
from .openfoam import write_openfoam_u_file
from .regime_diagram import compute_regime_point, plot_borghi_peters_diagram, regime_point_to_dict
from .solver import run_simulation
from .types import NS2dTimeseries


def _parse_csv_ints(text: str) -> list[int]:
    return [int(part) for part in text.split(",") if part.strip()]


def _parse_csv_floats(text: str) -> list[float]:
    return [float(part) for part in text.split(",") if part.strip()]


def _add_flame_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mechanism", required=True)
    parser.add_argument("--fuel", required=True)
    parser.add_argument("--oxidizer", required=True)
    parser.add_argument("--phi", type=float, required=True)
    parser.add_argument("--Tu", type=float, required=True)
    parser.add_argument("--Pu", type=float, required=True)
    parser.add_argument("--width", type=float, default=0.03)
    parser.add_argument("--transport-model", default="mixture-averaged")
    parser.add_argument("--loglevel", type=int, default=0)


def _build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""
    parser = argparse.ArgumentParser(prog="nslab2d")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run NS2dLab simulation")
    run.add_argument("--backend", choices=["cpu", "gpu"], default="cpu")
    run.add_argument("--N", type=int, default=128)
    run.add_argument("--dt", type=float, default=0.1)
    run.add_argument("--simutime-seconds", type=float, default=50.0)
    run.add_argument("--nu", type=float, default=1e-4)
    run.add_argument("--output", required=True)
    run.add_argument("--save-field-npz", default=None, help="Optional path to save the final velocity field snapshot")
    run.add_argument("--fftw-threads", type=int, default=None)

    cmp_ = sub.add_parser("compare-reference", help="Compare two NS2dLab-style .mat files")
    cmp_.add_argument("--reference", required=True)
    cmp_.add_argument("--candidate", required=True)

    info = sub.add_parser("device-info", help="Report CUDA/CuPy device information")
    info.add_argument("--json", action="store_true", help="Emit JSON only")

    compare = sub.add_parser("compare-backends", help="Run the same case on CPU and GPU and compare outputs")
    compare.add_argument("--N", type=int, default=128)
    compare.add_argument("--dt", type=float, default=0.1)
    compare.add_argument("--simutime-seconds", type=float, default=5.0)
    compare.add_argument("--nu", type=float, default=1e-4)
    compare.add_argument("--fftw-threads", type=int, default=None)

    benchmark = sub.add_parser("benchmark", help="Benchmark one backend over several grid sizes")
    benchmark.add_argument("--backend", choices=["cpu", "gpu"], required=True)
    benchmark.add_argument("--N", required=True, help="Comma-separated grid sizes, e.g. 64,128,256")
    benchmark.add_argument("--dt", required=True, help="Comma-separated timesteps matched to --N")
    benchmark.add_argument("--simutime-seconds", type=float, default=5.0)
    benchmark.add_argument("--nu", type=float, default=1e-4)
    benchmark.add_argument("--fftw-threads", type=int, default=None)

    validate = sub.add_parser("validate-manuscript-cases", help="Run CPU↔GPU comparisons for manuscript-scale cases")
    validate.add_argument("--output", default=None, help="Optional JSON output path")

    hit = sub.add_parser("hit-stats", help="Compute HIT statistics from a saved velocity field")
    hit.add_argument("--field-npz", required=True)
    hit.add_argument("--output", default=None, help="Optional JSON output path")

    flame = sub.add_parser("flame-properties", help="Compute laminar flame properties with Cantera")
    _add_flame_args(flame)
    flame.add_argument("--output", default=None, help="Optional JSON output path")

    regime = sub.add_parser("regime-diagram", help="Compute and plot a turbulent flame regime point")
    regime.add_argument("--field-npz", required=True)
    _add_flame_args(regime)
    regime.add_argument("--uprime-definition", choices=["component_rms", "planar_rms"], default="component_rms")
    regime.add_argument("--thickness-definition", choices=["delta_alpha", "delta_T"], default="delta_alpha")
    regime.add_argument("--output", required=True, help="PNG output path for the regime diagram")
    regime.add_argument("--json-output", default=None, help="Optional JSON output path")
    regime.add_argument("--annotate", default="case")

    ofu = sub.add_parser("export-openfoam-u", help="Export a saved 2D velocity field to an OpenFOAM 7 U file")
    ofu.add_argument("--field-npz", required=True)
    ofu.add_argument("--case-dir", required=True)
    ofu.add_argument("--time-dir", default="0")
    ofu.add_argument("--ordering", choices=["x-fastest", "y-fastest"], default="x-fastest")
    ofu.add_argument("--boundary-json", default=None, help="Optional JSON file describing boundaryField patches")
    return parser


def main() -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "run":
        cfg = NS2dConfig(
            N=args.N,
            dt=args.dt,
            simutime_seconds=args.simutime_seconds,
            nu=args.nu,
            backend=args.backend,
            fftw_threads=args.fftw_threads,
        )
        result = run_simulation(cfg)
        ts = NS2dTimeseries(
            Ekin=result.backend.to_numpy(result.timeseries.Ekin),
            Diss=result.backend.to_numpy(result.timeseries.Diss),
            Time=result.backend.to_numpy(result.timeseries.Time),
            ElapsedTime=result.timeseries.ElapsedTime,
        )
        save_timeseries(Path(args.output), cfg, ts)
        if args.save_field_npz is not None:
            save_velocity_field_npz(
                args.save_field_npz,
                U=result.backend.to_numpy(result.fields.U),
                V=result.backend.to_numpy(result.fields.V),
                dx=result.fields.dx,
                metadata={"case_name": cfg.case_name, "N": cfg.N, "dt": cfg.dt, "simutime_seconds": cfg.simutime_seconds},
            )
        print(
            json.dumps(
                {
                    "case_name": cfg.case_name,
                    "backend": cfg.backend,
                    "elapsed_time_seconds": result.timeseries.ElapsedTime,
                    "output": str(args.output),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "compare-reference":
        metrics = compare_mat_timeseries(args.reference, args.candidate)
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0

    if args.command == "device-info":
        payload = {"gpu_available": gpu_is_available()}
        if payload["gpu_available"]:
            payload.update(get_gpu_info())
        print(json.dumps(payload, indent=2 if not args.json else None, sort_keys=not args.json))
        return 0

    if args.command == "compare-backends":
        cfg = NS2dConfig(
            N=args.N,
            dt=args.dt,
            simutime_seconds=args.simutime_seconds,
            nu=args.nu,
            fftw_threads=args.fftw_threads,
        )
        comparison = compare_cpu_gpu(cfg)
        payload = {
            "config": {
                "N": comparison.config.N,
                "dt": comparison.config.dt,
                "simutime_seconds": comparison.config.simutime_seconds,
                "nu": comparison.config.nu,
            },
            "cpu_elapsed_time_seconds": comparison.cpu_elapsed_time_seconds,
            "gpu_elapsed_time_seconds": comparison.gpu_elapsed_time_seconds,
            "metrics": comparison.metrics,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "benchmark":
        N_values = _parse_csv_ints(args.N)
        dt_values = _parse_csv_floats(args.dt)
        results = benchmark_backend(
            backend=args.backend,
            N_values=N_values,
            dt_values=dt_values,
            simutime_seconds=args.simutime_seconds,
            nu=args.nu,
            fftw_threads=args.fftw_threads,
        )
        payload = [
            {
                "backend": entry.backend,
                "N": entry.N,
                "dt": entry.dt,
                "simutime_seconds": entry.simutime_seconds,
                "nu": entry.nu,
                "elapsed_time_seconds": entry.elapsed_time_seconds,
            }
            for entry in results
        ]
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "validate-manuscript-cases":
        payload = validate_manuscript_cases()
        if args.output is not None:
            Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "hit-stats":
        field = load_velocity_field_npz(args.field_npz)
        stats = compute_hit_stats(field["U"], field["V"], field["dx"], field["dy"])
        payload = asdict(stats)
        if args.output is not None:
            Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "flame-properties":
        props = compute_laminar_flame_properties(
            mechanism=args.mechanism,
            fuel=args.fuel,
            oxidizer=args.oxidizer,
            phi=args.phi,
            T_u=args.Tu,
            P_u=args.Pu,
            width=args.width,
            transport_model=args.transport_model,
            loglevel=args.loglevel,
        )
        payload = flame_properties_to_dict(props)
        if args.output is not None:
            Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "regime-diagram":
        field = load_velocity_field_npz(args.field_npz)
        stats = compute_hit_stats(field["U"], field["V"], field["dx"], field["dy"])
        props = compute_laminar_flame_properties(
            mechanism=args.mechanism,
            fuel=args.fuel,
            oxidizer=args.oxidizer,
            phi=args.phi,
            T_u=args.Tu,
            P_u=args.Pu,
            width=args.width,
            transport_model=args.transport_model,
            loglevel=args.loglevel,
        )
        point = compute_regime_point(
            stats,
            props,
            uprime_definition=args.uprime_definition,
            thickness_definition=args.thickness_definition,
        )
        plot_borghi_peters_diagram(
            point,
            output_path=args.output,
            annotate=args.annotate,
            title="Borghi/Peters-style turbulent flame regime diagram",
        )
        payload = {
            "hit_stats": asdict(stats),
            "flame_properties": flame_properties_to_dict(props),
            "regime_point": regime_point_to_dict(point),
            "figure": str(args.output),
        }
        if args.json_output is not None:
            Path(args.json_output).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "export-openfoam-u":
        field = load_velocity_field_npz(args.field_npz)
        boundary_patches = None
        if args.boundary_json is not None:
            boundary_patches = json.loads(Path(args.boundary_json).read_text(encoding="utf-8"))
        path = write_openfoam_u_file(
            field["U"],
            field["V"],
            case_dir=args.case_dir,
            time_dir=args.time_dir,
            ordering=args.ordering,
            boundary_patches=boundary_patches,
        )
        print(json.dumps({"path": str(path)}, indent=2))
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
