# Tutorials

> **Documentation map:** [README](../README.md) · [Getting Started](GETTING_STARTED.md) · **Tutorials** · [Crease Format](CREASE_FORMAT.md) · [Simulation](SIMULATION.md) · [Evaluation](EVALUATION.md) · [API Reference](API_REFERENCE.md) · [Architecture](ARCHITECTURE.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Glossary](GLOSSARY.md) · [Contributing](CONTRIBUTING.md)

Step-by-step recipes that build on each other. Every snippet assumes the package is installed (see [GETTING_STARTED.md](GETTING_STARTED.md)) and starts with:

```python
from origami_engine import (
    Crease,
    build_pattern,
    evaluate_individual,
    evaluate_population,
    load_creases_from_json,
    load_default_creases,
    normalize_creases,
    plot_pattern,
    run_simulation,
    save_creases_to_json,
)
```

## Tutorial 1 — Inspect a crease pattern without simulating

`build_pattern` turns raw creases into a validated face graph. This is pure geometry (Shapely) and does **not** need MuJoCo.

```python
creases = load_default_creases()
pat = build_pattern(creases)

print(pat.valid)  # True
print(pat.n_faces)  # 16 polygonal faces
print(pat.n_loops)  # 9 loop edges (non-tree edges, closed by equality constraints)
print(pat.root)  # index of the largest-area face (the free root body)
print(max(pat.depth.values()))  # depth of the hinge spanning tree
```

If the pattern is invalid, `pat.valid` is `False` and `pat.reason` says why (e.g. `"sliver face (area ...)"`, `"faces do not tile the sheet"`, `"disconnected faces"`). See [CREASE_FORMAT.md](CREASE_FORMAT.md) for the full list.

Runnable version: `python examples/03_inspect_pattern.py` (from a source checkout).

## Tutorial 2 — Run your first simulation

```python
result = run_simulation(load_default_creases(), duration=8.0, fold_duration=3.0, vibrate=True)
```

`result` is a `SimulationResult`:

| Field | Meaning |
|---|---|
| `result.model` / `result.data` | Final `mujoco.MjModel` / `MjData` state |
| `result.pattern` | The validated `Pattern` |
| `result.info` | `{"hinges": [...], "targets": np.ndarray, "n_faces", "n_hinges", "n_loops"}` |
| `result.initial_centroid` / `result.final_centroid` | 2D paper centroid (mean XY of all non-table geoms) before/after |

Parameters worth knowing (defaults in parentheses): `duration` (8.0 s of simulated time), `fold_duration` (3.0 s smoothstep ramp over which actuator targets go from 0 to full), `vibrate` (True), `amp_x`/`amp_z` (0.0 / 0.0013 m), `freq_hz` (75.0 Hz). See [SIMULATION.md](SIMULATION.md) for the internals.

## Tutorial 3 — Score a pattern (fitness)

```python
score = evaluate_individual(
    load_default_creases(),
    duration=8.0,
    trajectory=(1.0, 0.0, 0.0),  # measure displacement along +x
    fold_duration=3.0,
)
print(score)  # forward displacement in meters (float)
```

Ask for the details dict instead of just the float:

```python
details = evaluate_individual(load_default_creases(), duration=8.0, return_details=True)
# keys: displacement, initial_centroid, final_centroid, duration, trajectory, n_faces, n_loops
```

`trajectory` accepts a 2D or 3D direction vector, or an (N, 2)/(N, 3) waypoint array (direction = last − first), normalized internally. See [EVALUATION.md](EVALUATION.md).

## Tutorial 4 — Save and load crease patterns as JSON

```python
import tempfile, pathlib

creases = load_default_creases()
with tempfile.TemporaryDirectory() as tmp:
    path = pathlib.Path(tmp) / "my_pattern.json"
    save_creases_to_json(creases, path, angle_unit="degree")  # human-readable angles
    loaded = load_creases_from_json(path)  # validated against the JSON Schema

print(len(loaded), loaded[0])  # 24 Crease(p1=(0.2, 0.0), p2=(0.45, 0.25), angle=-0.785...)
```

`normalize_creases` also accepts a file path or a list of dicts directly, so you can pass any of these forms straight into `run_simulation` / `evaluate_individual`. The JSON format and schema are documented in [CREASE_FORMAT.md](CREASE_FORMAT.md).

Runnable version: `python examples/02_json_input.py`.

## Tutorial 5 — Define a custom pattern in Python

Creases are 2D segments on the unit sheet (`S = 1.0`). The crease set must tile the square into valid polygons:

```python
import numpy as np

v_fold = np.deg2rad(-45)  # mountain (negative)
m_fold = np.deg2rad(45)  # valley (positive)

creases = [
    Crease((0.0, 0.5), (0.5, 0.5), m_fold),
    Crease((0.5, 0.5), (1.0, 0.5), v_fold),
]
pat = build_pattern(creases)
print(pat.valid, pat.n_faces)  # True 2
```

Always check `pat.valid` before simulating — `run_simulation` raises `ValueError("invalid crease pattern: ...")` otherwise. Design rules and common failure reasons: [CREASE_FORMAT.md](CREASE_FORMAT.md).

## Tutorial 6 — Evaluate a population (e.g. a genetic algorithm)

```python
population = [load_default_creases(), load_default_creases(), load_default_creases()]

# Sequential (workers=1, default):
scores = evaluate_population(population, duration=4.0, workers=1)

# Parallel across processes (each individual is a full MuJoCo simulation):
scores = evaluate_population(population, duration=4.0, workers=4, error_policy="raise")
# error_policy="nan" returns float('nan') for failed individuals instead of raising

best = max(zip(scores, population), key=lambda t: t[0])
print("best fitness:", best[0])
```

Results keep the input order. See [EVALUATION.md](EVALUATION.md) for parallel semantics and a GA loop sketch.

Runnable version: `python examples/04_evaluate_population.py`.

## Tutorial 7 — Plot a pattern and save the figure

```python
import matplotlib

matplotlib.use("Agg")  # headless: no display needed
import matplotlib.pyplot as plt
from origami_engine import plot_pattern

creases = load_default_creases()
pat = build_pattern(creases)
plot_pattern(creases, pat)  # draws; under Agg, show() does not block
plt.gcf().savefig("my_pattern.png", dpi=150, bbox_inches="tight")
```

Style: Mountain = crimson dashed, Valley = royalblue dash-dot, each crease labelled with its fold angle in degrees, face indices in gray, loop edges marked with a black `x`. The repo ships a pre-rendered version at `docs/crease_pattern_plot.png`.

Runnable version: `python examples/05_plot_pattern.py`.

## Tutorial 8 — Render a folding video

Two ways:

**Console script** (installed with the package):

```bash
origami-render        # writes individual_simulation.mp4 + render_report.json
                      # into the current working directory, wherever that is
```

**From Python**, so you control inputs, duration, and the output path:

```python
from origami_engine.render_individual import trace_simulation, export_video

trace = trace_simulation(load_default_creases(), duration=10.0, fold_duration=3.0, fps=24)
print(trace["forward_displacement"])
export_video(trace["frames"], "folding.mp4", fps=24)  # True if MP4, False if it fell back to GIF
```

Details (camera, frame capture, MP4/GIF fallback, report JSON): [SIMULATION.md](SIMULATION.md).

## Tutorial 9 — Get the raw MuJoCo XML

Everything the engine builds is a standard MJCF XML string, so you can inspect or post-process it with plain MuJoCo:

```python
import mujoco
from origami_engine import build_pattern, generate_xml, load_default_creases

creases = load_default_creases()
pat = build_pattern(creases)
xml, info = generate_xml(pat, creases)

with open("model.xml", "w") as f:
    f.write(xml)

model = mujoco.MjModel.from_xml_string(xml)  # standard MuJoCo API from here on
data = mujoco.MjData(model)
```

The XML structure (bodies, hinges, equality constraints, actuators, table) is documented in [SIMULATION.md](SIMULATION.md).

## See also

- [GETTING_STARTED.md](GETTING_STARTED.md) — installation methods (pip / uv / source)
- [CREASE_FORMAT.md](CREASE_FORMAT.md) — crease & JSON format reference
- [SIMULATION.md](SIMULATION.md) — model generation, stepping loop, rendering
- [EVALUATION.md](EVALUATION.md) — fitness functions in depth
- [API_REFERENCE.md](API_REFERENCE.md) — every public function signature
- [README.md](../examples/README.md) — the runnable scripts behind these tutorials (in `examples/`)
