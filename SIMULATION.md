# Simulation Pipeline & Rendering

> **Documentation map:** [README](README.md) · [Getting Started](GETTING_STARTED.md) · [Tutorials](TUTORIALS.md) · [Crease Format](CREASE_FORMAT.md) · **Simulation** · [Evaluation](EVALUATION.md) · [API Reference](API_REFERENCE.md) · [Architecture](ARCHITECTURE.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Glossary](GLOSSARY.md) · [Contributing](CONTRIBUTING.md)

This document explains what happens inside `run_simulation`, how the MuJoCo XML model is generated, what the physical constants mean, and how video rendering works.

## Pipeline overview

```
creases (Crease list | dict list | JSON path)
   │  normalize_creases()                     (serialization.py — coerce + validate)
   ▼
build_pattern(creases) → Pattern             (geometry.py — Shapely face graph + spanning tree)
   │  generate_xml(pat, creases)              (model.py — MJCF XML string + info dict)
   ▼
mujoco.MjModel.from_xml_string(xml)           (requires mujoco — see backend.py import guard)
mujoco.MjData(model)
   │  run_simulation(): step loop             (dynamics.py — ctrl ramp + table vibration + mj_step)
   ▼
SimulationResult(model, data, pattern, info, initial_centroid, final_centroid)
```

## Model generation — `generate_xml(pat, creases, name="origami_free", coll_thick=None)`

Returns `(xml: str, info: dict)`. The XML is standard MJCF; you can save it and open it in the MuJoCo viewer (see Tutorial 9 in [TUTORIALS.md](TUTORIALS.md)).

Global settings emitted into the XML:

```xml
<compiler angle="radian"/>
<option timestep="0.001" gravity="0 0 -9.81" integrator="implicitfast"/>
<default><geom solref="0.004 1" solimp="0.9 0.95 0.001"/></default>
```

- **Timestep** 1 ms with the `implicitfast` integrator; gravity −9.81 along z.
- Solver defaults `solref="0.004 1"`, `solimp="0.9 0.95 0.001"` for contact softness.

### Bodies and joints — one body per face

- Each face `i` becomes `<body name="face_{i}">` containing a triangulated **triangular-prism mesh** per triangle (visual `mesh` geoms with density `PAPER_MASS / (S² · 2·THICK) = 1000`, `contype=conaffinity=1`, `condim=3`, friction `MU_PAPER 0.005 0.0001 = 0.3 0.005 0.0001`). Materials alternate `paper_A` / `paper_B` by tree depth for visualization.
- The **root face** gets a `<freejoint name="root"/>` and is placed at its centroid, offset to `z = Z0 = THICK + 0.001`.
- Every non-root face is attached to its parent through the tree edge:
  - `<joint name="crease_{h}" type="hinge">` — axis along the shared edge, `range="±π"`, damping `DAMPING=0.003`, armature 0.001. This is the fold hinge.
  - Two `<joint name="stretch_a_{h}" / stretch_n_{h}" type="slide">` spring joints along the edge direction and its in-plane normal (`stiffness=STRETCH_K=5e4`, `damping=STRETCH_DAMP=50`, `range="±STRETCH_MAX=±1e-4"`) that keep the panel edges from stretching.
- **Loop edges** (edges not in the spanning tree) are closed with `<equality><connect body1 body2 ananchor=... solref="0.005 1" solimp="0.95 0.99 0.001"/></equality>` at both endpoints, so the paper stays a single connected sheet.

### Actuators — fold targets

One `<position name="fold_{h}" joint="crease_{h}" kp="2.0" kv="0.15" ctrlrange="±π" forcerange="±2.0"/>` per hinge (`KP`, `KV`, `FORCE_MAX`). The per-hinge target is `clip(sgn * crease.angle, ±MAX_FOLD)` where `sgn` mirrors the angle depending on which side of the hinge the child face lies (`MAX_FOLD = 0.98π`). Targets are returned in `info["targets"]` and the hinge metadata in `info["hinges"]` (`name`, `face`, `edge`, `target`).

`info` dict keys: `hinges`, `targets` (np.ndarray), `n_faces`, `n_hinges`, `n_loops`.

### Support table

```xml
<body name="table" pos="0 0 -0.05">
  <joint name="table_x" type="slide" axis="1 0 0" damping="0"/>
  <joint name="table_z" type="slide" axis="0 0 1" damping="0"/>
  <geom name="ground" type="box" size="5 5 0.05" ... friction="0.5 0.005 0.0001" mass="1000"/>
</body>
```

The table is kinematically vibrated (see below) and the paper rests on it via contacts (`MU_TABLE = 0.5`).

### Optional thin-collision mode

`coll_thick=<float>` splits each mesh into a visual geom (`contype=0`) and a thinner collision geom (transparent, `COLL_THICK = THICK·0.1 = 1e-5` by default) — useful when paper self-collision at full thickness causes jitter.

## The step loop — `run_simulation(creases, duration=8.0, fold_duration=3.0, vibrate=True, amp_x=VIB_AMP_X, amp_z=VIB_AMP_Z, freq_hz=VIB_FREQ)`

1. `normalize_creases` → `build_pattern`; raises `ValueError` if `duration <= 0` or the pattern is invalid (`"invalid crease pattern: {reason}"`).
2. `generate_xml` → `MjModel.from_xml_string` → `MjData`; all hinge qpos zeroed; `initial_centroid = paper_centroid(model, data)`.
3. While `data.time < duration`:
   - `t = min(data.time / fold_duration, 1.0)`, smoothstep `s = t²(3 − 2t)`; actuator commands `data.ctrl[:] = s * targets` (targets ramp from 0 to full over `fold_duration` seconds).
   - If `vibrate`: `drive_table(model, data, data.time, amp_x, amp_z, freq_hz)` sets the table slide joints kinematically:
     `qpos = amp·sin(2π f t)`, `qvel = amp·2π f·cos(2π f t)` for `table_x` and `table_z`.
   - `mujoco.mj_step(model, data)`.
4. Stability check: non-finite `qpos` → `FloatingPointError("unstable simulation: ...")`.
5. Returns `SimulationResult` with `final_centroid = paper_centroid(model, data)`.

### `paper_centroid(model, data)`

Mean XY position of `data.geom_xpos` over all geoms whose body is **not** the table — i.e. the centroid of the paper sheet in the plane. Raises `ValueError` if no paper geoms exist.

### `drive_table(model, data, t, amp_x=0.0, amp_z=0.0013, freq_hz=75.0)`

Kinematic sinusoidal vibration of the support table (see step 3). Defaults: `VIB_AMP_X=0.0`, `VIB_AMP_Z=0.0013` m, `VIB_FREQ=75.0` Hz. The README video table shows lower/high/higher amplitude & frequency variants.

## Physical & solver constants

Defined in `origami_engine/constants.py` and re-exported at package level:

| Constant | Value | Role |
|---|---|---|
| `S` | `1.0` | Sheet side length (unit square) |
| `THICK` | `1e-4` | Paper thickness (m) |
| `PAPER_MASS` | `0.2` | Total sheet mass (kg) |
| `Z0` | `1.1e-3` | Initial paper height above world origin |
| `MIN_FACE_AREA` | `1e-4` | Reject faces smaller than this (sliver detection) |
| `MAX_FOLD` | `0.98π ≈ 3.079` | Clip for hinge target angles |
| `KP`, `KV` | `2.0`, `0.15` | Position-actuator gains per hinge |
| `DAMPING` | `0.003` | Hinge joint damping |
| `FORCE_MAX` | `2.0` | Actuator force limit |
| `MU_PAPER` / `MU_TABLE` | `0.3` / `0.5` | Friction coefficients |
| `VIB_FREQ` / `VIB_AMP_X` / `VIB_AMP_Z` | `75.0` / `0.0` / `0.0013` | Table vibration defaults |
| `EQ_SOLREF` / `EQ_SOLIMP` | `"0.005 1"` / `"0.95 0.99 0.001"` | Equality-constraint solver params |
| `STRETCH_K` / `STRETCH_DAMP` / `STRETCH_MAX` | `5e4` / `50` / `1e-4` | Panel stretch spring limits |
| `K_PANEL` / `D_PANEL` / `MAX_STRAIN` / `COLL_THICK` | `1e5` / `50` / `0.005` / `1e-5` | Panel stiffness/damping, strain cap, thin collision thickness |
| `M` / `V` | `+π/4` / `−π/4` | Canonical ±45° fold angles used by reference patterns |

## Rendering — `origami_engine/render_individual.py`

- `trace_simulation(creases, duration=2.0, fold_duration=3.0, fps=24, trajectory=(1,0,0), vibrate=True, amp_x, amp_z, freq_hz)` — runs the same pipeline as `run_simulation` but renders frames with `mujoco.Renderer` (720×720; camera lookat `[0.5, 0.5, 0.05]`, distance 2.5, azimuth 90°, elevation −30°). Returns a dict with `frames`, `initial_centroid`, `final_centroid`, `forward_displacement`, `model`, `data`, `info`, `pattern`.
- `export_video(frames, output_path, fps=24)` — writes MP4 via `imageio` + `libx264` (`-pix_fmt yuv420p`); on failure falls back to an animated `.gif` and returns `False` (returns `True` when the MP4 was written). Raises `ValueError` if `frames` is empty.
- `main()` — the body of the **`origami-render` console script** (`pyproject.toml` → `[project.scripts]`). Uses the default pattern, `duration=20.0`, `fold_duration=1e-6`, `vibrate=True`; writes `individual_simulation.mp4` and a `render_report.json` (crease source, duration, centroids, rendered vs. evaluator forward displacement, video path) and prints the report.

Output paths are resolved against the **current working directory** (`OUTPUT_VIDEO` / `OUTPUT_REPORT` in `render_individual.py`), so `origami-render` writes `individual_simulation.mp4` + `render_report.json` wherever you run it — identically for a source checkout and a PyPI wheel install (see the note in [GETTING_STARTED.md](GETTING_STARTED.md)). Use `trace_simulation` + `export_video` directly when you need full programmatic control over the output path.

## Performance notes

- Cost scales with `duration / timestep` (8 s ⇒ 8000 `mj_step` calls) and with the number of faces (each face = one body + meshes).
- `evaluate_population(..., workers=N)` parallelizes whole simulations across processes — see [EVALUATION.md](EVALUATION.md).
- For batch research workloads, the MJX (JAX) backend of MuJoCo is the natural next step; the XML emitted here is directly consumable by `mujoco.mjx`.

## See also

- [EVALUATION.md](EVALUATION.md) — turning a `SimulationResult` into a fitness score
- [API_REFERENCE.md](API_REFERENCE.md) — exact signatures of `run_simulation`, `generate_xml`, `drive_table`, `paper_centroid`, `trace_simulation`, `export_video`
- [ARCHITECTURE.md](ARCHITECTURE.md) — module responsibilities and data flow
- [experiments/TIMELINE.md](experiments/TIMELINE.md) — how these physics parameters were tuned in the prototype notebooks
