from __future__ import annotations

from pathlib import Path

from scipy.io import loadmat

from nslab2d.config import NS2dConfig
from nslab2d.io import save_timeseries
from nslab2d.types import NS2dTimeseries


def test_save_timeseries(tmp_path: Path):
    out = tmp_path / "case.mat"
    cfg = NS2dConfig(N=16, dt=0.1, simutime_seconds=0.2)
    ts = NS2dTimeseries(Ekin=[1.0, 2.0], Diss=[0.1, 0.2], Time=[0.0, 0.2], ElapsedTime=1.5)
    save_timeseries(out, cfg, ts)
    raw = loadmat(out)
    assert raw["Ekin"].shape == (2, 1)
    assert raw["Diss"].shape == (2, 1)
    assert raw["Time"].shape == (2, 1)
