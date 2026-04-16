from __future__ import annotations

from nslab2d.backend import gpu_is_available


def test_gpu_is_available_returns_bool():
    value = gpu_is_available()
    assert isinstance(value, bool)
