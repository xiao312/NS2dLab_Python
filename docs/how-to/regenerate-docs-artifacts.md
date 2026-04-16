# Regenerate documentation artifacts

Use this guide to rebuild the generated figures and JSON assets shown in the docs site.

## Run the artifact-generation script

```bash
python scripts/generate_docs_artifacts.py
```

## What the script does

The script regenerates:

- validation figures
- backend benchmark figures and JSON summaries
- flame/HIT example artifacts
- an OpenFOAM `U` snippet used in the documentation site

## Where the tracked outputs go

The script refreshes files under:

```text
docs/assets/generated/
```

## Before committing

After regenerating artifacts, run:

```bash
pytest -q
mkdocs build --strict
```
