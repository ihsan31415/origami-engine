# Getting Started

> **Documentation map:** [README](README.md) · **Getting Started** · [Tutorials](TUTORIALS.md) · [Crease Format](CREASE_FORMAT.md) · [Simulation](SIMULATION.md) · [Evaluation](EVALUATION.md) · [API Reference](API_REFERENCE.md) · [Architecture](ARCHITECTURE.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Glossary](GLOSSARY.md) · [Contributing](CONTRIBUTING.md)

This guide covers every supported way to install **origami-engine** and how to use the package afterwards, regardless of which method you chose.

- PyPI package name: `origami-engine`
- Python import name: `origami_engine`
- Console command installed by the package: `origami-render`
- Python versions: **3.10 or 3.11** (`requires-python = ">=3.10"`)
- Runtime dependencies: `mujoco>=2.3`, `numpy>=1.24`, `shapely>=2.0`, `matplotlib>=3.7`, `imageio[ffmpeg]>=2.34`, `jsonschema>=4.18`

## Installation methods at a glance

| # | Method | Command | Best for |
|---|---|---|---|
| 1 | `pip` into a virtualenv (from PyPI) | `pip install origami-engine[dev]` | Most users; standard, well-understood workflow |
| 2 | `uv` (from PyPI) | `uv pip install origami-engine[dev]` or `uv add origami-engine` | Fast installs, projects that use `uv`, CI |
| 3 | Editable install from a source clone | `pip install -e ".[dev]"` (or `uv pip install -e ".[dev]"`) | Contributors; running tests, examples, rendering into the repo |
| 4 | No virtualenv ("quick test") | `pip install --user origami-engine` or `uv tool install origami-engine` | Trying the library once; CLI-only use via `uvx` |

The **only** difference between methods is *how the files land on your machine* and *what extra files you get*. Once installed, the Python API (`import origami_engine`) and the `origami-render` command are identical in every case.

## Method 1 — pip + virtualenv (from PyPI)

The conventional approach. A virtualenv keeps the project's dependencies isolated from your system Python.

```bash
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install "origami-engine[dev]"
```

- `[dev]` adds `pytest`, `pytest-cov`, `ruff`, `mypy`, and `pre-commit`. Omit it (`pip install origami-engine`) for a runtime-only install.
- Verify the install:

```bash
python -c "import origami_engine; print(origami_engine.__version__)"
# 0.1.0
```

### Using the package after a pip install

```python
from origami_engine import load_default_creases, build_pattern, run_simulation

creases = load_default_creases()
pat = build_pattern(creases)
print(pat.valid, pat.n_faces, pat.n_loops)  # True 16 9

result = run_simulation(creases, duration=8.0)
print(result.final_centroid)
```

Run the bundled renderer as a console script (installed into the active environment's `bin/`):

```bash
origami-render
```

> **Note on output paths:** `origami-render` always writes `individual_simulation.mp4` and `render_report.json` into the **current working directory** — identically for a source checkout and a PyPI wheel. Run it from whatever directory you want the MP4 in. To control the path programmatically, use `trace_simulation` + `export_video` directly (see [SIMULATION.md](SIMULATION.md)).

> **Note on packaged files:** the wheel ships the package including the JSON Schema (`origami_engine/schemas/`) **and** the reference crease pattern (`origami_engine/crease_patterns/reference_miura_4x4.json`), so `load_default_creases()` reads the same 24-crease / 16-face / 9-loop Miura-ori pattern in every install method (see [CREASE_FORMAT.md](CREASE_FORMAT.md)). The wheel does not ship the repo's `tests/`, `examples/`, or the repo-root `crease_patterns/` folder — those are development assets.

## Method 2 — uv (from PyPI)

[uv](https://docs.astral.sh/uv/) is a fast, Rust-based Python package and project manager. It is a drop-in replacement for `pip`/`venv` and additionally manages project environments and lockfiles.

### 2a. uv with a virtualenv (closest to Method 1)

```bash
uv venv .venv                 # create a virtualenv (like python -m venv)
. .venv/bin/activate
uv pip install "origami-engine[dev]"
```

`uv pip install` targets the *active* environment and is interface-compatible with `pip install`, so everything in Method 1 applies unchanged.

### 2b. uv-managed project (uses `pyproject.toml` + lockfile)

If your own project has a `pyproject.toml`, declare the dependency and let uv resolve and lock it:

```bash
uv init                       # once, in your project
uv add "origami-engine[dev]"  # adds to pyproject.toml + creates uv.lock
uv run python your_script.py  # runs inside the project environment, no activation needed
```

Difference vs 2a: uv records the exact resolved versions in `uv.lock` (reproducible installs, `uv sync`), while `uv pip install` into a bare venv behaves like pip and does not create a lockfile.

### 2c. Ephemeral / CLI-only usage

```bash
uv run --with origami-engine python -c "import origami_engine; print(origami_engine.__version__)"
uv tool install origami-engine   # installs the origami-render CLI globally
uvx origami-render               # run the CLI without installing it
```

Use 2c for one-off commands or when you only need the `origami-render` command and do not want a project environment.

### pip vs uv — what actually differs

| Aspect | pip | uv |
|---|---|---|
| Speed | Standard | Much faster (parallel resolution/download in Rust) |
| Virtualenv creation | `python -m venv` | `uv venv` |
| Install into active env | `pip install ...` | `uv pip install ...` (same flags) |
| Project + lockfile | `pip install` + manual `requirements.txt` / `pip freeze` | `uv add` + `uv.lock` + `uv sync` |
| Run without activating | — | `uv run ...` |
| One-off tool run | `pipx run ...` | `uvx ...` / `uv tool install ...` |

The installed package and its behavior are identical; choose uv for speed and reproducible project environments, pip when you want the most conventional, universally documented workflow.

## Method 3 — editable install from source (for development)

Clone the repository and install in editable mode so code changes take effect immediately and the repo's extras (tests, examples, crease patterns, Makefile targets) are available:

```bash
git clone https://github.com/ihsan31415/origami-engine.git
cd origami-engine

python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
# or, with uv:
#   uv venv .venv && . .venv/bin/activate && uv pip install -e ".[dev]"
```

Then:

```bash
make test                                  # pytest -q (with coverage)
make example                               # python origami_engine/example.py
make render                                # python origami_engine/render_individual.py
make examples                              # run every script in examples/
make lint && make typecheck                # ruff + mypy
python examples/01_evaluate_reference.py   # individual examples
```

From a source checkout, `make render` writes `individual_simulation.mp4` and `render_report.json` into the repository root (the Makefile runs from there, and `origami-render` writes to the current working directory), and `load_default_creases()` reads the packaged `origami_engine/crease_patterns/reference_miura_4x4.json`, which is byte-identical to the repo-root `crease_patterns/reference_miura_4x4.json` (guarded by a test).

## Method 4 — no virtualenv (quick test)

```bash
pip install --user origami-engine     # installs into the user site-packages
python -c "import origami_engine; print(origami_engine.__version__)"
```

or, with uv, install the CLI as an isolated tool:

```bash
uv tool install origami-engine
uvx origami-render
```

Use this only for a quick evaluation. Prefer a virtualenv (Methods 1–3) for real work, because `--user` installs share the user site-packages and can conflict with other projects.

## Your first simulation (any method)

```python
from origami_engine import (
    build_pattern,
    evaluate_individual,
    load_default_creases,
    plot_pattern,
    run_simulation,
)

# 1. Load the reference Miura-ori pattern (24 creases)
creases = load_default_creases()

# 2. Reconstruct and validate the face graph
pat = build_pattern(creases)
assert pat.valid, pat.reason
print(f"faces={pat.n_faces} loop_edges={pat.n_loops}")  # faces=16 loop_edges=9

# 3. Visualize the flat crease pattern (Mountain = crimson dashed, Valley = blue dash-dot)
plot_pattern(creases, pat)

# 4. Run the MuJoCo folding simulation (8 s at 1 ms timestep)
result = run_simulation(creases, duration=8.0)
print(result.info["n_hinges"], "hinges driven")
print("centroid moved:", result.final_centroid - result.initial_centroid)

# 5. Score it: forward displacement along +x
score = evaluate_individual(creases, duration=8.0, trajectory=(1.0, 0.0, 0.0), fold_duration=3.0)
print(f"forward displacement: {score:.6f}")
```

## Upgrading and uninstalling

```bash
pip install -U origami-engine        # upgrade          | uv pip install -U origami-engine
pip uninstall origami-engine         # uninstall        | uv pip uninstall origami-engine
```

## Next steps

- Step-by-step recipes: [TUTORIALS.md](TUTORIALS.md)
- Crease input format and JSON Schema: [CREASE_FORMAT.md](CREASE_FORMAT.md)
- How the simulation is built and rendered: [SIMULATION.md](SIMULATION.md)
- Fitness / population evaluation: [EVALUATION.md](EVALUATION.md)
- Full API signatures: [API_REFERENCE.md](API_REFERENCE.md)
- Install/runtime problems: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
