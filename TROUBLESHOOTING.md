# Troubleshooting

> **Documentation map:** [README](README.md) · [Getting Started](GETTING_STARTED.md) · [Tutorials](TUTORIALS.md) · [Crease Format](CREASE_FORMAT.md) · [Simulation](SIMULATION.md) · [Evaluation](EVALUATION.md) · [API Reference](API_REFERENCE.md) · [Architecture](ARCHITECTURE.md) · **Troubleshooting** · [Glossary](GLOSSARY.md) · [Contributing](CONTRIBUTING.md)

Common problems and their fixes, grouped by stage.

## Installation

**`ERROR: Package 'origami-engine' requires a different Python`** — the package needs Python ≥ 3.10 (CI tests 3.10 and 3.11). Create the environment with a supported interpreter: `python3.11 -m venv .venv` or `uv venv --python 3.11`.

**`uv pip install` says "No virtual environment found"** — `uv pip` targets the *active* environment. Either activate one (`. .venv/bin/activate`) or use project mode (`uv add origami-engine` + `uv run ...`). See [GETTING_STARTED.md](GETTING_STARTED.md), Method 2.

**`mujoco` fails to install / import on an exotic platform** — MuJoCo ships manylinux/macOS/windows wheels; on other platforms install fails at pip time. On headless Linux servers the import works but **rendering** needs a GL backend — see below.

**`imageio` cannot find ffmpeg** — the dependency is `imageio[ffmpeg]`, which bundles an ffmpeg binary, so no system ffmpeg is needed. If you installed without the extra (`pip install imageio`), reinstall with `pip install "imageio[ffmpeg]"`. `export_video` falls back to GIF if MP4 encoding fails.

## Import errors

**`ModuleNotFoundError: No module named 'origami_engine'`** — the package is not installed in the interpreter you are using. Check `which python` / `python -c "import sys; print(sys.executable)"` and reinstall into that environment (`pip install origami-engine` or `pip install -e ".[dev]"` from a checkout).

**`RuntimeError: MuJoCo is required ...` from `run_simulation` / `generate_xml`** — expected behavior of the import guard (`backend.py`) when `mujoco` is not installed. Pure-geometry functions (`build_pattern`, `normalize_creases`, `load_creases_from_json`, `plot_pattern`, constants) still work without it.

## Headless / no-display rendering

`origami-render` and `trace_simulation` need OpenGL. On a server without a display, set one of:

```bash
export MUJOCO_GL=osmesa    # software rendering (pip install osmesa is not needed; mujoco bundles it)
# or
export MUJOCO_GL=egl       # GPU servers with EGL
export MUJOCO_GL=disable   # skip rendering entirely (simulation still runs)
```

`plot_pattern` uses Matplotlib; on headless machines use the Agg backend (`matplotlib.use("Agg")`) and save with `plt.gcf().savefig(...)` instead of relying on `plt.show()` (see [TUTORIALS.md](TUTORIALS.md), Tutorial 7).

## Invalid crease patterns

`build_pattern` returns `pat.valid == False` (and `run_simulation` raises `ValueError("invalid crease pattern: {reason}")`) for:

| `reason` | Cause | Fix |
|---|---|---|
| `no faces` | Creases don't partition the sheet | Add creases that connect boundary to boundary or form closed loops |
| `sliver face (area …)` | A face smaller than `MIN_FACE_AREA = 1e-4` | Snap nearly-coincident endpoints together; avoid tiny triangles |
| `faces do not tile the sheet` | Face areas don't sum to `S²` within 1e-6 | Crease endpoints must lie **exactly** on other creases or the boundary — floating-point offsets break tiling |
| `disconnected faces` | Face adjacency graph is disconnected | Connect every panel to the rest through shared edges |

See [CREASE_FORMAT.md](CREASE_FORMAT.md) for the full format rules and the JSON Schema failure modes (`ValueError("invalid crease JSON: ...")` from `load_creases_from_json`).

## Simulation stability

**`FloatingPointError: unstable simulation: non-finite joint coordinates produced.`** — the fold exploded (usually extreme target angles, too-long `duration`, or aggressive vibration). Try: smaller fold angles (`|angle| ≤ MAX_FOLD = 0.98π` is enforced, but smaller is more stable), shorter `duration`, `vibrate=False` or smaller `amp_z`/`freq_hz`, or `generate_xml(..., coll_thick=...)` thin-collision mode.

**Simulation is slow** — cost is `duration / 0.001` steps (8 s ⇒ 8000 `mj_step` calls) plus mesh contact. Use short `duration` while iterating; parallelize populations with `evaluate_population(..., workers=N)`.

## PyPI install vs source checkout

| Behavior | PyPI wheel | Source checkout (`pip install -e .`) |
|---|---|---|
| `import origami_engine`, `origami-render` CLI | identical | identical |
| `load_default_creases()` | embedded fallback pattern | reads `crease_patterns/reference_miura_4x4.json` (same topology: 24 creases / 16 faces / 9 loops) |
| `tests/`, `examples/`, `Makefile` targets | not shipped | available (`make test`, `make examples`, …) |
| `origami-render` output files | written under the environment's `site-packages` | written to the repo root |

## Upgrading / uninstalling

```bash
pip install -U origami-engine     # upgrade        | uv pip install -U origami-engine
pip uninstall origami-engine      # remove         | uv pip uninstall origami-engine
uv tool uninstall origami-engine  # if installed via `uv tool install`
```

## Getting help

- Search/open an issue: <https://github.com/ihsan31415/origami-engine/issues>
- When reporting, include: Python version, install method (pip/uv/wheel/editable), the exact command, the full traceback, and a minimal crease list that reproduces the problem.
- For usage questions, check [TUTORIALS.md](TUTORIALS.md) and [GLOSSARY.md](GLOSSARY.md) first.
