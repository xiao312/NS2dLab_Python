"""Command-line interface for NS2dLab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backend import get_gpu_info, gpu_is_available
from .compare import benchmark_backend, compare_cpu_gpu, validate_manuscript_cases
from .config import NS2dConfig
from .io import compare_mat_timeseries, save_timeseries
from .solver import run_simulation
from .types import NS2dTimeseries


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
        N_values = [int(part) for part in args.N.split(",") if part.strip()]
        dt_values = [float(part) for part in args.dt.split(",") if part.strip()]
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

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
