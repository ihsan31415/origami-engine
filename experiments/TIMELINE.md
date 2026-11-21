# Experimental Timeline

> Part of the documentation set — traceable from the root [README.md](../README.md) via [ARCHITECTURE.md](../ARCHITECTURE.md).

This folder preserves the **prototyping stage** of the simulator, before the code was modularized into `origami_engine/`. The four Jupyter notebooks document how the fold physics was discovered and tuned: crease generation, collision handling, viscoelastic spring/damping behavior, and the fixes that stopped the paper mesh from tearing at extreme fold angles.

The notebooks are **archived, not executed**. They are not required to run the simulator and are not imported by the package.

## Contents

| File | What it is |
|---|---|
| [`prototype_notebooks.zip`](prototype_notebooks.zip) | The four original prototyping notebooks (`GEN_1` … `GEN_4`), zipped to keep the repository light |
| `TIMELINE.md` | This document — the phase-by-phase history |

## Timeline

### Phase 1 — Base mechanics exploration
**Notebook:** `GEN_1_creasing_and_vibrations_simulation_.ipynb`

- Parse 2D point arrays into primitive hinges.
- Validate torque/position actuators for programmatic angle folding.
- Inject stochastic vibration parameters on the support table to evaluate dynamic folding behavior.

### Phase 2 — Contact layer optimization
**Notebook:** `GEN_2_improving_sim_collision.ipynb`

- Prevent self-intersection artifacts during high-angle folds.
- Tune MuJoCo collision primitives (geom margins/gaps, `contype`/`conaffinity`).
- Override global contact solver settings to isolate adjacent non-rigid paper faces.

### Phase 3 — Viscoelastic dynamics tuning
**Notebook:** `GEN_3_improving_sim_physics_spring,_damp_and_collision_test.ipynb`

- Add linear spring coefficients (`stiffness`) across folding hinges (the `stretch_*` slide joints in the current model).
- Tune joint damping to remove extreme kinematic oscillations.
- Stress-test collision robustness against heightened viscoelastic forces.

### Phase 4 — Production stabilization and tear fixes
**Notebook:** `GEN_4_optimizing_W_close_successed_to_fix_the_tear.ipynb`

- Fix mesh tearing caused by numerical divergence at near-closed angles.
- Adjust constraint solver parameters (`solref`, `solimp`) for high-tension areas.
- Snap joints closed without distorting the mesh.

## How the experiments map to the engine today

Phase 4 is the baseline that became the current engine. The tuned values now live in code:

| Prototype concept (notebooks) | Current home |
|---|---|
| Hinge actuation with target fold angles | `model.py` — `<position name="fold_{h}" … kp kp kv>` actuators + `info["targets"]` |
| Edge stretch springs | `model.py` — `stretch_a_{h}` / `stretch_n_{h}` slide joints; constants `STRETCH_K`, `STRETCH_DAMP`, `STRETCH_MAX` in `constants.py` |
| Solver softness tuning | `constants.py` — `EQ_SOLREF`, `EQ_SOLIMP`, default geom `solref="0.004 1"`, `solimp="0.9 0.95 0.001"` |
| Tear fix at extreme angles | `constants.py` — `MAX_FOLD = 0.98π` clip in `model.py`; `FloatingPointError` stability check in `dynamics.py` |
| Table vibration | `dynamics.py` — `drive_table()`; constants `VIB_FREQ=75 Hz`, `VIB_AMP_Z=0.0013`, `VIB_AMP_X=0.0` |
| Crease generation from 2D points | `geometry.py` — `build_pattern()` (Shapely polygonize + validation) and `serialization.py` (JSON I/O + schema) |
| Collision layering | `model.py` — `coll_thick` thin-collision mode (`COLL_THICK`), paper/table friction `MU_PAPER=0.3`, `MU_TABLE=0.5` |

## Inspecting the notebooks

Unzip the archive locally (the extracted folder is git-ignored):

```bash
unzip experiments/prototype_notebooks.zip -d experiments/notebooks
. .venv/bin/activate
pip install jupyter
jupyter notebook experiments/notebooks
```

## See also

- [README.md](../README.md) — project overview, simulation output, documentation map
- [ARCHITECTURE.md](../ARCHITECTURE.md) — current module layout and data flow
- [SIMULATION.md](../SIMULATION.md) — the production simulation pipeline these notebooks led to
- [../origami_engine/constants.py](../origami_engine/constants.py) and [../origami_engine/model.py](../origami_engine/model.py) — where the tuned constants live
