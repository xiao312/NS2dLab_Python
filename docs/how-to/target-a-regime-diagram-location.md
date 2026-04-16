# Target a regime-diagram location

Use this guide to generate a synthetic divergence-free turbulence field that approximately matches a desired location on the regime diagram.

## Workflow

The implemented workflow is:

1. compute target `u'` and `l_t` from `S_L`, `delta_L`, and the desired diagram coordinates
2. search over `N`, `L`, and either spectral peak `k0` or modal index `m`
3. generate random divergence-free spectral fields for each candidate
4. rescale each candidate to the target `u'`
5. optionally evolve the field and select the sample closest to the target pair
6. optionally save reusable visual artifacts for the best field and the search history

## Step 1: compute target values explicitly

```bash
nslab2d regime-targets \
  --Sl 0.40 \
  --deltaL 5e-4 \
  --lt-over-deltaL 20 \
  --uprime-over-Sl 5
```

## Step 2: tune a field directly from `S_L` and `delta_L`

```bash
nslab2d tune-regime-field \
  --Sl 0.40 \
  --deltaL 5e-4 \
  --lt-over-deltaL 20 \
  --uprime-over-Sl 5 \
  --N-values 128,256,512 \
  --L-values 6.283185307179586,12.566370614359172 \
  --k0-values 2,3,4,5,6,8,10 \
  --bandwidth 1.5 \
  --output-field-npz results/tuned_field.npz \
  --output-json results/tuned_field.json \
  --output-search-plot results/tuned_field_search.png \
  --output-artifacts-dir results/tuned_field_artifacts
```

## Step 3: tune a field from combustion inputs

```bash
nslab2d tune-regime-field \
  --mechanism gri30.yaml \
  --fuel CH4 \
  --oxidizer 'O2:1.0, N2:3.76' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325 \
  --lt-over-deltaL 20 \
  --uprime-over-Sl 5 \
  --N-values 128,256,512 \
  --L-values 6.283185307179586,12.566370614359172 \
  --evolve-seconds 2 \
  --output-field-npz results/tuned_field.npz \
  --output-json results/tuned_field.json \
  --output-search-plot results/tuned_field_search.png
```

## Step 4: target a regime point and plot requested vs achieved locations

```bash
nslab2d target-regime-point \
  --Sl 0.40 \
  --deltaL 5e-4 \
  --lt-over-deltaL 20 \
  --uprime-over-Sl 5 \
  --N-values 128,256,512,1024 \
  --L-values 6.283185307179586,12.566370614359172 \
  --k0-values 2,3,4,5,6,8,10 \
  --output-field-npz results/targeted_field.npz \
  --output-json results/targeted_field.json \
  --output-search-plot results/targeted_field_search.png \
  --output-artifacts-dir results/targeted_field_artifacts
```

## Step 5: search in modal-index space when `L` varies

When you search over multiple domain lengths, modal indices are often easier to reason about than raw physical `k0` values.

```bash
nslab2d target-regime-point \
  --mechanism h2o2.yaml \
  --fuel H2 \
  --oxidizer 'O2:1.0, AR:5.0' \
  --phi 1.0 \
  --Tu 300 \
  --Pu 101325 \
  --lt-over-deltaL 10 \
  --uprime-over-Sl 100 \
  --backend gpu \
  --N-values 128,256,512,1024 \
  --L-values 5e-4,1e-3,2e-3,5e-3,1e-2 \
  --mode-values 2,3,4,5,6,8,10,12,16 \
  --bandwidth-modes 1.5 \
  --output-field-npz results/h2_target_10_100.npz \
  --output-json results/h2_target_10_100.json \
  --output-search-plot results/h2_target_10_100_search.png \
  --output-artifacts-dir results/h2_target_10_100_artifacts
```

This makes the solver evaluate `k0 = m (2\pi/L)` automatically for each tested `L`.

## Notes

- matching `u'` is easy because the field amplitude is rescaled directly
- matching `l_t` is harder and is controlled by the combination of `N`, `L`, and `k0` or modal index `m`
- `--mode-values` is usually the more robust choice when `L` changes across the search
- the tuning-history JSON stores every tested `N`, `L`, `k0`, optional modal index `m`, sampled time, measured `u'`, measured `l_t`, and score
- `--output-artifacts-dir` writes a final curl plot, a top-history curl montage, and a regime diagram with target/best/history markers
- the search plot shows all candidates in `(u'/S_L, l_t/\delta_L)` space with the best candidate highlighted
- exact hits are not guaranteed on the first try, but the search usually gets close
- optional evolution can produce a more natural developed field before handoff

## Related pages

- [Flame/HIT methodology](../explanation/flame-hit-methodology.md)
- [CLI reference](../reference/cli-reference.md)
