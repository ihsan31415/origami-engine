# API Reference

> **Documentation map:** [README](README.md) · [Getting Started](GETTING_STARTED.md) · [Tutorials](TUTORIALS.md) · [Crease Format](CREASE_FORMAT.md) · [Simulation](SIMULATION.md) · [Evaluation](EVALUATION.md) · **API Reference** · [Architecture](ARCHITECTURE.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Glossary](GLOSSARY.md) · [Contributing](CONTRIBUTING.md)

Complete reference for the public API of `origami_engine` (version `0.1.0`). All names below are importable from the package root:

```python
import origami_engine

origami_engine.__all__  # full export list
```

## Import paths

| Import style | Example | Notes |
|---|---|---|
| Package root (recommended) | `from origami_engine import Crease, run_simulation` | Stable public surface |
| Focused module | `from origami_engine.dynamics import run_simulation` | Fine for new code |
| Legacy facade | `from origami_engine.simulation import Crease, ...` | Backward-compatible re-exports (also re-exports all constants) |

**MuJoCo import guard** (`origami_engine/backend.py`): the `mujoco` import is guarded. Geometry, serialization, plotting, and constants work without MuJoCo installed; `generate_xml`, `run_simulation`, `drive_table`, `paper_centroid`, and `render_individual` call `require_mujoco(...)`, which raises a helpful `RuntimeError` if `mujoco` is missing.

## Domain types (`origami_engine.types`)

### `Crease` — frozen dataclass

```python
Crease(p1: tuple[float, float], p2: tuple[float, float], angle: float)
```

A single crease segment. `p1`/`p2` are 2D points in sheet coordinates (`0..S`, `S=1.0`); `angle` is the signed target fold angle in **radians** — negative = mountain, positive = valley.

### `Pattern` — dataclass

Returned by `build_pattern`. Fields: `valid: bool`, `reason: str`, `faces: list | None` (Shapely polygons), `edges: list[dict] | None` (each `{"i", "j", "p", "q", "crease"}`), `root: int`, `parent: dict`, `depth: dict`, `tree_edge: dict`, `loop_edges: list[int] | None`, `n_faces: int`, `n_loops: int`. See [CREASE_FORMAT.md](CREASE_FORMAT.md).

### `SimulationResult` — dataclass

Returned by `run_simulation`. Fields: `model` (`mujoco.MjModel`), `data` (`mujoco.MjData`), `pattern: Pattern`, `info: dict` (`hinges`, `targets`, `n_faces`, `n_hinges`, `n_loops`), `initial_centroid: np.ndarray` (2,), `final_centroid: np.ndarray` (2,).

## Pattern construction & I/O

### `build_pattern(creases) -> Pattern`

(`origami_engine.geometry`) Reconstruct polygonal faces and the spanning-tree hinge graph from a crease list. `creases` may be a `Crease` list, dict list, or JSON path (normalized internally is **not** done here — pass normalized creases or dicts with `p1/p2/angle`; see `normalize_creases`). Pure Shapely — no MuJoCo needed. Validation reasons: `"no faces"`, `"sliver face (area …)"`, `"faces do not tile the sheet"`, `"disconnected faces"`.

### `normalize_creases(creases) -> list[Crease]`

(`origami_engine.serialization`) Coerce a JSON path, list of `Crease`, or list of dicts into `list[Crease]`. Raises `ValueError` (`None`, empty, missing keys, bad item type) / `TypeError` (non-list input).

### `load_creases_from_json(path) -> list[Crease]`

Load and **schema-validate** a crease JSON file (both forms documented in [CREASE_FORMAT.md](CREASE_FORMAT.md)). `angle_unit` in `radian|radians|rad|degree|degrees|deg` (default radian; degrees converted via `np.deg2rad`). Raises `ValueError` on schema violation or missing keys (message includes the crease index).

### `save_creases_to_json(creases, path, angle_unit="radian") -> Path`

Serialize creases to JSON (object form with `angle_unit` + `creases`), creating parent dirs. `angle_unit` must be `"radian"` or `"degree"` (else `ValueError`). Angles are converted to the requested unit.

### `CREASE_SCHEMA`

The packaged JSON Schema (dict) loaded from `origami_engine/schemas/crease_pattern.schema.json` (shipped as package data). Use with `jsonschema.validate(payload, CREASE_SCHEMA)` in your own tooling.

## Reference patterns (`origami_engine.patterns`)

| Export | Description |
|---|---|
| `DEFAULT_PATTERN_JSON` | `Path` to `crease_patterns/reference_miura_4x4.json` **in a source checkout**; absent in an installed wheel |
| `load_default_creases() -> list[Crease]` | Load `DEFAULT_PATTERN_JSON` when present, else fall back to the embedded `reference_miura_render_creases()` (same 24-crease / 16-face / 9-loop topology) |
| `reference_miura_legacy_creases() -> list[Crease]` | Embedded legacy 4×4 Miura-ori crease list (used by tests/examples) |
| `reference_miura_render_creases() -> list[Crease]` | Embedded render-tuned Miura-ori crease list (used by the renderer) |

## Model generation (`origami_engine.model`)

### `generate_xml(pat, creases, name="origami_free", coll_thick=None) -> tuple[str, dict]`

Build the MJCF XML string for a validated `Pattern` (see [SIMULATION.md](SIMULATION.md) for the full structure). Parameters: `pat` — `Pattern` from `build_pattern`; `creases` — normalized creases (target angles are looked up by edge index); `name` — model name attribute; `coll_thick` — `None` for single-geom mode, or a thickness value enabling separate visual/collision geoms. Returns `(xml, info)` where `info = {"hinges": [{"name", "face", "edge", "target"}...], "targets": np.ndarray, "n_faces", "n_hinges", "n_loops"}`. Requires MuJoCo (raises `RuntimeError` via `require_mujoco` otherwise).

## Simulation (`origami_engine.dynamics`)

### `run_simulation(creases, duration=8.0, fold_duration=3.0, vibrate=True, amp_x=VIB_AMP_X, amp_z=VIB_AMP_Z, freq_hz=VIB_FREQ) -> SimulationResult`

Full pipeline: normalize → build pattern → generate XML → `MjModel`/`MjData` → step loop with smoothstep actuator ramp (`s = t²(3−2t)`, `ctrl = s·targets`) and optional sinusoidal table vibration → stability check. Raises `ValueError` (`duration <= 0`, invalid pattern) and `FloatingPointError` (non-finite qpos). See [SIMULATION.md](SIMULATION.md).

### `drive_table(model, data, t, amp_x=VIB_AMP_X, amp_z=VIB_AMP_Z, freq_hz=VIB_FREQ) -> None`

Kinematically vibrate the support table: sets `qpos = amp·sin(2πft)` and `qvel = amp·2πf·cos(2πft)` on the `table_x`/`table_z` slide joints. Defaults `amp_x=0.0`, `amp_z=0.0013`, `freq_hz=75.0`.

### `paper_centroid(model, data) -> np.ndarray`

Mean XY of `data.geom_xpos` over all geoms whose body is not `table`. Raises `ValueError` if no paper geoms exist.

## Evaluation (`origami_engine.evaluation`)

### `compute_forward_displacement(sim_result, trajectory=(1.0, 0.0, 0.0)) -> float`

`dot(final_centroid − initial_centroid, normalize(trajectory))`. `trajectory`: 2/3-vector direction or `(N,2)/(N,3)` waypoints (N ≥ 2, direction = last − first). Raises `ValueError` on malformed/zero/non-finite input. See [EVALUATION.md](EVALUATION.md).

### `evaluate_individual(creases, duration=8.0, trajectory=(1.0, 0.0, 0.0), fold_duration=3.0, vibrate=True, amp_x=VIB_AMP_X, amp_z=VIB_AMP_Z, freq_hz=VIB_FREQ, return_details=False) -> float | dict`

Run one simulation and return its forward displacement. With `return_details=True` returns a dict: `displacement`, `initial_centroid`, `final_centroid`, `duration`, `trajectory`, `n_faces`, `n_loops`.

### `evaluate_population(individuals, duration=8.0, trajectory=(1.0, 0.0, 0.0), fold_duration=3.0, vibrate=True, amp_x=VIB_AMP_X, amp_z=VIB_AMP_Z, freq_hz=VIB_FREQ, workers=1, error_policy="raise") -> list[float]`

Score a list of crease inputs. `workers=1` → sequential; `workers>1` → `ProcessPoolExecutor` (`max_workers = min(workers, len(individuals))`). `error_policy="raise"` wraps failures in `RuntimeError("individual {i} failed ...")`; `"nan"` yields `float("nan")` for failed slots. Order preserved.

## Visualization (`origami_engine.plotting`)

### `plot_pattern(creases, pat=None) -> None`

Matplotlib figure of the flat pattern: sheet rectangle, Mountain = crimson dashed / Valley = royalblue dash-dot, each crease labelled with its angle in degrees, face indices in gray, loop edges as black `x`, legend, equal aspect, title `"{N} creases | {M} faces | {K} loop edges (x)"` (or `"… | INVALID: {reason}"`). Calls `plt.show()`; under the Agg backend grab the figure with `plt.gcf()` and save it (see [TUTORIALS.md](TUTORIALS.md), Tutorial 7).

## Rendering script (`origami_engine.render_individual`)

Also installed as the **`origami-render`** console command (`[project.scripts]` in `pyproject.toml`).

| Function | Signature | Description |
|---|---|---|
| `trace_simulation` | `(creases, duration=2.0, fold_duration=3.0, fps=24, trajectory=(1,0,0), vibrate=True, amp_x, amp_z, freq_hz)` | Simulate + capture frames (720×720 `mujoco.Renderer`, camera lookat `[0.5,0.5,0.05]`, distance 2.5, azimuth 90, elevation −30). Returns dict with `frames`, centroids, `forward_displacement`, `model`, `data`, `info`, `pattern` |
| `export_video` | `(frames, output_path, fps=24) -> bool` | MP4 via imageio/libx264 (`yuv420p`); falls back to `.gif` (returns `False`). `ValueError` if no frames |
| `main` | `()` | CLI body: default pattern, `duration=20.0`, `fold_duration=1e-6`; writes `individual_simulation.mp4` + `render_report.json` and prints the report |

## Constants (`origami_engine.constants`)

All re-exported from the package root and from `origami_engine.simulation`:

| Constant | Value | Meaning |
|---|---|---|
| `S` | `1.0` | Sheet side length |
| `THICK` | `1e-4` | Paper thickness |
| `PAPER_MASS` | `0.2` | Sheet mass |
| `Z0` | `THICK + 0.001` | Initial paper z-offset |
| `MIN_FACE_AREA` | `1e-4 · S²` | Sliver-face rejection threshold |
| `MAX_FOLD` | `0.98π` | Hinge target clip |
| `KP` / `KV` | `2.0` / `0.15` | Hinge position-actuator gains |
| `DAMPING` | `0.003` | Hinge damping |
| `FORCE_MAX` | `2.0` | Actuator force limit |
| `MU_PAPER` / `MU_TABLE` | `0.3` / `0.5` | Friction coefficients |
| `VIB_FREQ` / `VIB_AMP_X` / `VIB_AMP_Z` | `75.0` / `0.0` / `0.0013` | Table vibration defaults |
| `EQ_SOLREF` / `EQ_SOLIMP` | `"0.005 1"` / `"0.95 0.99 0.001"` | Equality constraint solver params |
| `STRETCH_K` / `STRETCH_DAMP` / `STRETCH_MAX` | `5e4` / `50` / `1e-4` | Edge stretch spring params |
| `K_PANEL` / `D_PANEL` | `1e5` / `50` | Panel stiffness/damping |
| `MAX_STRAIN` / `COLL_THICK` | `0.005` / `1e-5` | Strain cap / thin collision thickness |
| `M` / `V` | `+π/4` / `−π/4` | Canonical ±45° angles used by the reference pattern builders (note: the `Crease.angle` sign convention is negative=mountain, positive=valley) |

## Complete workflow example

```python
from origami_engine import (
    build_pattern,
    evaluate_individual,
    load_default_creases,
    plot_pattern,
    run_simulation,
)

creases = load_default_creases()  # 24-crease Miura-ori reference
pat = build_pattern(creases)  # validate topology
assert pat.valid, pat.reason

plot_pattern(creases, pat)  # visualize the flat pattern

result = run_simulation(creases, duration=8.0)
print(result.info["n_faces"], "faces,", result.info["n_hinges"], "hinges")

score = evaluate_individual(creases, duration=8.0, trajectory=(1.0, 0.0, 0.0))
print(f"forward displacement: {score:.6f} m")
```

## See also

- [GETTING_STARTED.md](GETTING_STARTED.md) — installation (pip / uv / source) and first run
- [TUTORIALS.md](TUTORIALS.md) — nine step-by-step recipes
- [CREASE_FORMAT.md](CREASE_FORMAT.md) — crease & JSON schema reference
- [SIMULATION.md](SIMULATION.md) — XML model structure, step loop, rendering
- [EVALUATION.md](EVALUATION.md) — fitness functions and population evaluation
- [ARCHITECTURE.md](ARCHITECTURE.md) — module layout and data flow
