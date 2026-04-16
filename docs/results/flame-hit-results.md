# Flame/HIT results

This page demonstrates the current downstream combustion workflow using a generated NS2dLab velocity field.

## HIT statistics example

These values come from the generated example field:

| Quantity | Value |
|---|---:|
| `u'_component` | 0.01387 |
| `u'_planar` | 0.01961 |
| `l_t,x` | 0.36383 |
| `l_t,y` | 0.46844 |
| `l_t,mean` | 0.41614 |
| `k_2D` | 1.9228e-4 |

## Laminar flame properties example

The current lightweight docs example uses `h2o2.yaml` with `H2` fuel.

| Quantity | Value |
|---|---:|
| `S_L` | 2.31445 m/s |
| `alpha_u` | 4.4301e-5 m²/s |
| `delta_alpha` | 1.9141e-5 m |
| `delta_T` | 4.0310e-4 m |
| `T_b` | 2496.11 K |

## Regime diagram placement

![](../assets/generated/flame/regime_diagram.png)

| Quantity | Value |
|---|---:|
| `u'/S_L` | 5.991e-3 |
| `l_t/delta_L` | 2.174e4 |
| `Da` | 3.629e6 |
| `Ka` | 3.145e-6 |

## OpenFOAM export example

```text
--8<-- "assets/generated/openfoam/U_snippet.txt"
```
