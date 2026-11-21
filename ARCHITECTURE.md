# Architecture

> **Documentation map:** [README](README.md) · [Getting Started](GETTING_STARTED.md) · [Tutorials](TUTORIALS.md) · [Crease Format](CREASE_FORMAT.md) · [Simulation](SIMULATION.md) · [Evaluation](EVALUATION.md) · [API Reference](API_REFERENCE.md) · **Architecture** · [Troubleshooting](TROUBLESHOOTING.md) · [Glossary](GLOSSARY.md) · [Contributing](CONTRIBUTING.md)

## Overview

`origami_engine` is an **engineering library**, not a monolithic script. Each module has a single responsibility, and the pipeline is deliberately split so that geometry, I/O, and evaluation can be used without ever instantiating a MuJoCo model.

## Module map

| Module | Responsibility | Key exports |
|---|---|---|
| `backend.py` | Guarded `import mujoco` (works without MuJoCo for pure-geometry use) | `mujoco`, `require_mujoco`, `MUJOCO_IMPORT_ERROR` |
| `constants.py` | All physical/solver constants in one place | `S`, `THICK`, `PAPER_MASS`, `M`, `V`, `MAX_FOLD`, `KP`, `KV`, `VIB_*`, `EQ_*`, `STRETCH_*`, … (full table in [API_REFERENCE.md](API_REFERENCE.md)) |
| `types.py` | Domain dataclasses | `Crease`, `Pattern`, `SimulationResult` |
| `geometry.py` | Crease graph → validated face graph (Shapely): polygonize, sliver/tiling/connectivity checks, spanning tree, loop-edge detection | `build_pattern` |
| `model.py` | Validated `Pattern` → MJCF XML string (bodies, hinges, stretch joints, equality connects, actuators, vibrating table) | `generate_xml` |
| `dynamics.py` | Simulation execution: step loop, actuator ramp, table vibration, centroid tracking | `run_simulation`, `drive_table`, `paper_centroid` |
| `serialization.py` | Crease input normalization + JSON I/O, validated against the packaged JSON Schema | `normalize_creases`, `load_creases_from_json`, `save_creases_to_json`, `CREASE_SCHEMA` |
| `evaluation.py` | Fitness API: forward displacement, single & population scoring (sequential or process pool) | `compute_forward_displacement`, `evaluate_individual`, `evaluate_population` |
| `patterns.py` | Reusable reference crease patterns + default loader with embedded fallback | `load_default_creases`, `reference_miura_legacy_creases`, `reference_miura_render_creases`, `DEFAULT_PATTERN_JSON` |
| `plotting.py` | Reference-style crease-pattern plot (Mountain/Valley colors, angle labels, face indices, loop-edge markers) | `plot_pattern` |
| `simulation.py` | Backward-compatible facade re-exporting the core API + constants | `from origami_engine.simulation import ...` keeps old code working |
| `render_individual.py` | Render a pattern to MP4/GIF + JSON report; also the `origami-render` CLI | `trace_simulation`, `export_video`, `main` |
| `example.py` | Minimal evaluation demo (`make example`) | — |
| `schemas/crease_pattern.schema.json` | JSON Schema (draft 2020-12) for crease input files; shipped as package data | `CREASE_SCHEMA` |

## Data flow

```
                 ┌────────────────────────────────────────────────────────────┐
 crease input    │  Crease list · dict list · JSON path                       │
 (CREASE_FORMAT) │  normalize_creases()  ── schema-validated JSON load        │
                 └───────────────┬────────────────────────────────────────────┘
                                 ▼
                 ┌────────────────────────────┐
                 │  build_pattern()           │  Shapely: polygonize unit square,
                 │  → Pattern(valid, faces,  │  reject sliver/untiled/disconnected,
                 │    edges, tree, loops)     │  BFS spanning tree from largest face
                 └───────────────┬────────────┘
                                 ▼
                 ┌────────────────────────────┐
                 │  generate_xml()            │  face_i bodies, root freejoint,
                 │  → (xml, info)             │  hinge + stretch joints per tree edge,
                 │                            │  equality connect per loop edge,
                 │                            │  position actuators per hinge
                 └───────────────┬────────────┘
                                 ▼
                 ┌────────────────────────────┐
                 │  run_simulation()          │  MjModel/MjData, smoothstep ctrl ramp,
                 │  → SimulationResult        │  drive_table() vibration, mj_step loop,
                 │                            │  non-finite stability check
                 └───────────────┬────────────┘
                                 ▼
                 ┌────────────────────────────┐
                 │  evaluate_*()              │  forward displacement = centroid delta · dir
                 │  plot_pattern()            │  or visualization of the flat pattern
                 │  render_individual.py      │  or MP4 video + render_report.json
                 └────────────────────────────┘
```

## Design decisions

- **Library-first.** Everything is importable from `origami_engine`; scripts (`example.py`, `render_individual.py`, `examples/`) are thin entry points that bootstrap `sys.path` so they also run directly from a checkout.
- **Schema-driven input.** Crease JSON is validated against a packaged JSON Schema at load time; invalid files fail fast with `ValueError` instead of producing garbage simulations.
- **Geometry is decoupled from physics.** `build_pattern` needs only Shapely/NumPy, so pattern validation and plotting work even where MuJoCo cannot be installed; the MuJoCo import is guarded in `backend.py`.
- **Backward-compatible facade.** `origami_engine/simulation.py` re-exports the core API and all constants so pre-modularization imports keep working.
- **Deterministic scoring.** Fitness = projected displacement of the paper centroid between t=0 and t=duration, under fixed `duration`/`fold_duration`/`trajectory`/vibration settings; see [EVALUATION.md](EVALUATION.md).
- **Reproducible artifacts.** Rendering writes `individual_simulation.mp4` plus a machine-readable `render_report.json`.
- **Packaging.** `pyproject.toml` (setuptools) declares `origami-engine` with runtime deps (`mujoco`, `numpy`, `shapely`, `matplotlib`, `imageio[ffmpeg]`, `jsonschema`), a `dev` extra (pytest, pytest-cov, ruff, mypy, pre-commit), the `origami-render` console script, and ships the schema via `[tool.setuptools.package-data]`. Repo-only files (`tests/`, `examples/`, `crease_patterns/`) are intentionally not in the wheel; `load_default_creases()` falls back to an embedded pattern in that case.

## Project layout

```text
.
├── origami_engine/
│   ├── __init__.py            # public API re-exports + __version__
│   ├── backend.py             # mujoco import guard
│   ├── constants.py           # physical/solver constants
│   ├── types.py               # Crease, Pattern, SimulationResult
│   ├── geometry.py            # build_pattern (Shapely face graph)
│   ├── model.py               # generate_xml (MJCF)
│   ├── dynamics.py            # run_simulation, drive_table, paper_centroid
│   ├── serialization.py       # normalize/JSON I/O + CREASE_SCHEMA
│   ├── schemas/crease_pattern.schema.json
│   ├── evaluation.py          # fitness APIs
│   ├── patterns.py            # reference crease patterns
│   ├── plotting.py            # plot_pattern
│   ├── simulation.py          # backward-compatible facade
│   ├── render_individual.py   # video renderer + origami-render CLI
│   └── example.py             # minimal demo
├── examples/                  # runnable snippets (01–05) + README.md
├── crease_patterns/           # reference_miura_4x4.json (repo only)
├── experiments/               # archived prototype notebooks + TIMELINE.md
├── tests/                     # pytest suite (test_evaluation.py, conftest.py)
├── docs/                      # crease_pattern_plot.png
├── .github/workflows/ci.yml   # lint + typecheck + test matrix; PyPI publish
├── Makefile                   # venv/install/test/lint/format/typecheck/render/...
├── pyproject.toml             # package metadata, deps, tool config
├── README.md                  # landing page (banner, badges, simulation output)
├── GETTING_STARTED.md … CONTRIBUTING.md   # documentation set (see map above)
└── LICENSE
```

## Dependencies and why

| Dependency | Used by | Purpose |
|---|---|---|
| `mujoco>=2.3` | `model`, `dynamics`, `render_individual` | Physics engine; XML model + stepping + rendering |
| `numpy>=1.24` | everywhere | Arrays, math |
| `shapely>=2.0` | `geometry`, `model` | Planar geometry: polygonize, intersections, triangulation |
| `matplotlib>=3.7` | `plotting` | Crease-pattern figures |
| `imageio[ffmpeg]>=2.34` | `render_individual` | MP4/GIF export (bundles an ffmpeg binary) |
| `jsonschema>=4.18` | `serialization` | Crease JSON validation |

Dev extra: `pytest`, `pytest-cov`, `ruff`, `mypy`, `pre-commit`.

## Quality gates & CI

- **ruff** — lint + format, line-length 120, target py310 (`pyproject.toml [tool.ruff]`).
- **mypy** — `files = ["origami_engine"]`, py310 (`[tool.mypy]`).
- **pytest** — `testpaths = ["tests"]`, coverage of `origami_engine` via addopts (`--cov`, term + XML).
- **pre-commit** — ruff, ruff-format, mypy hooks (`.pre-commit-config.yaml`).
- **GitHub Actions** (`.github/workflows/ci.yml`) — on push/PR to `main`, matrix Python 3.10/3.11: ruff check, ruff format --check, mypy, pytest; a separate job builds the wheel (`python -m build`) and publishes to PyPI with `pypa/gh-action-pypi-publish` (Trusted Publishing).

Details for contributors: [CONTRIBUTING.md](CONTRIBUTING.md).

## See also

- [SIMULATION.md](SIMULATION.md) — model XML structure, step loop, rendering internals
- [CREASE_FORMAT.md](CREASE_FORMAT.md) — input format, schema, pattern validity rules
- [EVALUATION.md](EVALUATION.md) — fitness semantics, population evaluation
- [API_REFERENCE.md](API_REFERENCE.md) — every public signature
- [experiments/TIMELINE.md](experiments/TIMELINE.md) — how the physics constants evolved
