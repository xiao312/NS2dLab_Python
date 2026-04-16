# Flame/HIT methodology

This page explains the logic behind the turbulence-to-combustion workflow.

The detailed workflow page remains here:

- [Flame-in-HIT workflow](../flame_hit_workflow.md)

## What is being combined

The workflow combines two kinds of information:

1. a fully evolved 2D turbulence field from NS2dLab
2. laminar flame properties from a 1D Cantera flame calculation

## Why these quantities are used

The regime-diagram placement is based on standard turbulent premixed-flame quantities:

- turbulence intensity `u'`
- integral length scale `l_t`
- laminar flame speed `S_L`
- laminar flame thickness `delta_L`

From these, the workflow computes:

- `u'/S_L`
- `l_t/delta_L`
- `Da`
- `Ka`

## Important limitation

The Borghi/Peters framework is classically associated with 3D turbulent premixed flames.
Applying it to 2D HIT is therefore an approximation that should be treated as a qualitative classification aid, not a strict 3D equivalence.
