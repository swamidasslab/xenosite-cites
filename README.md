# template-py-project

Starter Python package for **swamidasslab** conventions: uv, `src/` layout, hatch-vcs, pytest (parallel, coverage, doctests, Hypothesis), Ruff, mypy, towncrier, and GitHub Actions.

## Start a new repo from this template

```bash
cd ~/Workspaces
gh repo create {org}/{name} --template swamidasslab/template-py-project --private --clone
```

Then rename `template-py-project` / `template_py_project` and the GitHub URLs in `pyproject.toml`. Org is **swamidass** or **swamidasslab**.

This template is a **package** (no committed `uv.lock` / `.python-version`). For a production app, start from the template, then commit those pins and switch CI to `uv sync --frozen`.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy src
```

Version comes from git tags (`vX.Y.Z`). See [docs/release.md](docs/release.md). PyPI publishing is opt-in.

## Usage

```python
from template_py_project import hello

hello()
```

More in [docs/usage.md](docs/usage.md).
