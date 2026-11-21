# Contributing

> **Documentation map:** [README](README.md) · [Getting Started](GETTING_STARTED.md) · [Tutorials](TUTORIALS.md) · [Crease Format](CREASE_FORMAT.md) · [Simulation](SIMULATION.md) · [Evaluation](EVALUATION.md) · [API Reference](API_REFERENCE.md) · [Architecture](ARCHITECTURE.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Glossary](GLOSSARY.md) · **Contributing**

Thanks for your interest in contributing! You can help with code, tests, documentation, example crease patterns, or bug reports.

## Development setup

Clone the repo and install in **editable** mode with the dev extras:

```bash
git clone https://github.com/ihsan31415/origami-engine.git
cd origami-engine

# with pip
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

# or with uv (equivalent, faster)
uv venv .venv && . .venv/bin/activate
uv pip install -e ".[dev]"
```

`[dev]` adds `pytest`, `pytest-cov`, `ruff`, `mypy`, and `pre-commit`. Editable mode means your edits are live immediately and the repo-only assets (`tests/`, `examples/`, `crease_patterns/`) are in place.

## Everyday commands (Makefile)

| Command | What it runs |
|---|---|
| `make help` | List all targets |
| `make venv` / `make install` | Create `.venv` / install package + dev deps editable |
| `make test` | `pytest -q` (coverage of `origami_engine` is configured via addopts) |
| `make example` | `python origami_engine/example.py` (minimal evaluation demo) |
| `make render` | `python origami_engine/render_individual.py` (writes `individual_simulation.mp4` + `render_report.json` in the repo root) |
| `make examples` | Run every `examples/0*.py` script |
| `make lint` | `ruff check .` + `ruff format --check .` |
| `make format` | `ruff format .` + `ruff check --fix .` |
| `make typecheck` | `mypy origami_engine` |
| `make clean` | Remove generated artifacts and caches |

Without make, the equivalents are plain commands, e.g. `python -m pytest -q`, `python -m ruff check .`.

## Pre-commit hooks

Install once per clone; hooks then run on every commit:

```bash
pre-commit install
```

Configured hooks (`.pre-commit-config.yaml`): `ruff --fix`, `ruff-format`, and `mypy` (with the runtime deps installed in the hook env, scoped to `origami_engine/`).

## Code style & type checking

- **ruff** with `line-length = 120`, `target-version = "py310"` (`pyproject.toml [tool.ruff]`).
- **mypy** with `files = ["origami_engine"]`, `python_version = "3.10"`.
- Prefer the package-root imports in new code (`from origami_engine import ...`); keep `origami_engine/simulation.py` as the backward-compatible facade — add new exports to the focused module **and** the facade **and** `__init__.py`'s `__all__`.
- Public functions should raise `ValueError`/`TypeError` with messages that name the offending index/key (see `serialization.py` for the pattern).

## Tests

- Suite: `tests/test_evaluation.py` with fixtures in `tests/conftest.py` (`simple_creases`, `default_creases`, `default_pattern`, `tmp_json`).
- Config: `testpaths = ["tests"]`, addopts enable `--cov=origami_engine --cov-report=term-missing --cov-report=xml`.
- Add or update tests for any new behavior: input validation, JSON round-trips, pattern validity reasons, evaluation semantics (order preservation, `error_policy`), and a smoke run with short `duration`.
- Run `make lint && make typecheck && make test` before opening a PR.

## Continuous integration

`.github/workflows/ci.yml` runs on push/PR to `main`:

1. **lint-and-test** — matrix over Python 3.10 and 3.11: `ruff check .`, `ruff format --check .`, `mypy origami_engine --config-file pyproject.toml`, `pytest -q` (after `pip install -e ".[dev]"`).
2. **publish-to-pypi** — builds the sdist/wheel with `python -m build` and publishes via `pypa/gh-action-pypi-publish` (PyPI Trusted Publishing, OIDC).

## Submitting changes

1. Fork the repository and create a focused branch: `feat/...`, `fix/...`, `docs/...`, `chore/...`.
2. Make your changes in small, reviewable commits.
3. Add/update tests and documentation for any behavior change.
4. Run the quality gates locally (`make lint`, `make typecheck`, `make test`).
5. Open a pull request against `main` with a clear description and, for behavior changes, a minimal repro or example.

## Documentation contributions

- The documentation set lives in the repo root (`README.md`, `GETTING_STARTED.md`, `TUTORIALS.md`, `CREASE_FORMAT.md`, `SIMULATION.md`, `EVALUATION.md`, `API_REFERENCE.md`, `ARCHITECTURE.md`, `TROUBLESHOOTING.md`, `GLOSSARY.md`, `CONTRIBUTING.md`) plus `examples/README.md` and `experiments/TIMELINE.md`.
- Keep the **documentation map** nav line at the top of each root doc intact and add new pages to it, so every `.md` stays traceable from `README.md`.
- **Do not modify** the `README.md` banner (`<h1>` title + badge HTML block) or the simulation video tables, and do not edit `CHANGELOG.md` (maintained at release time).
- Keep docs accurate to the code: signatures in [API_REFERENCE.md](API_REFERENCE.md) must match the source; run the examples when you change behavior.

## Project layout

See [ARCHITECTURE.md](ARCHITECTURE.md) for the module responsibilities, data-flow diagram, and directory tree.

## Code of conduct

Be respectful and constructive in issues and reviews. Assume good intent, give actionable feedback, and keep discussions focused on the change.
