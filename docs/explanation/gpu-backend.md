# GPU backend

This page explains the role of the GPU backend in the project.

The detailed operational notes remain here:

- [GPU backend notes](../gpu.md)

## Design intent

The GPU backend is not a different solver. It is the same solver logic with a different array and FFT implementation.

That design gives the project two important properties:

1. the CPU path remains the correctness reference
2. CPU↔GPU comparisons are meaningful because the algorithm is shared

## Why double precision is used

The GPU backend uses double precision in order to preserve consistency with the CPU reference path and the original MATLAB-style numerical intent.

## What users should expect

- small cases may not favor the GPU
- larger FFT-dominated cases can favor the GPU strongly
- close numerical agreement is expected, not bitwise identity
