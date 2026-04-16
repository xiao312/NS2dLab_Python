# Contributing

The main contribution guide lives in the repository root as `CONTRIBUTING.md`.

For now, please read that file directly on GitHub or in your local checkout:

- [Repository contributing guide](https://github.com/xiao312/NS2dLab_Python/blob/main/CONTRIBUTING.md)

Typical local workflow:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e '.[full]'
uv pip install -e '.[docs]'
pytest -q
mkdocs serve
```

Before opening a pull request, it is good practice to run:

```bash
pytest -q
mkdocs build --strict
```
