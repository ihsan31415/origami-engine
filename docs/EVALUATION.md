# Evaluation & Fitness

> **Documentation map:** [README](../README.md) · [Getting Started](GETTING_STARTED.md) · [Tutorials](TUTORIALS.md) · [Crease Format](CREASE_FORMAT.md) · [Simulation](SIMULATION.md) · **Evaluation** · [API Reference](API_REFERENCE.md) · [Architecture](ARCHITECTURE.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Glossary](GLOSSARY.md) · [Contributing](CONTRIBUTING.md)

The engine's fitness signal is the **forward displacement** of the paper centroid: how far the sheet's center of mass travels along a requested direction while it folds.

## The fitness function

`compute_forward_displacement(sim_result, trajectory=(1.0, 0.0, 0.0))` → `float`

```
direction = normalize(trajectory)
delta     = sim_result.final_centroid − sim_result.initial_centroid
score     = dot(delta, direction)        # 2D: uses x,y · 3D: delta embedded in 3D, z=0
```

`paper_centroid` (see [SIMULATION.md](SIMULATION.md)) is the mean XY of all non-table geom positions, so the score is a planar displacement in meters (sheet is 1 m × 1 m).

### `trajectory` semantics

| Input | Interpretation |
|---|---|
| 2-vector `(x, y)` or 3-vector `(x, y, z)` | Direction of travel; normalized internally |
| `(N, 2)` / `(N, 3)` waypoint array (N ≥ 2) | Direction = `last − first`, normalized |

Errors (`ValueError`): scalar input, wrong vector length, fewer than 2 waypoints, zero/non-finite/non-finite-norm direction. `None` defaults to `(1, 0, 0)`.

## `evaluate_individual(...)`

```python
evaluate_individual(
    creases,  # Crease list | dict list | JSON path
    duration=8.0,  # simulated seconds (must be > 0)
    trajectory=(1.0, 0.0, 0.0),  # fitness direction (see above)
    fold_duration=3.0,  # smoothstep ramp time for hinge targets
    vibrate=True,  # support-table vibration on/off
    amp_x=VIB_AMP_X,  # 0.0
    amp_z=VIB_AMP_Z,  # 0.0013
    freq_hz=VIB_FREQ,  # 75.0
    return_details=False,
)
```

- Returns a `float` (the forward displacement), or a `dict` when `return_details=True` with keys: `displacement`, `initial_centroid`, `final_centroid`, `duration`, `trajectory` (normalized), `n_faces`, `n_loops`.
- Internally: `normalize_creases` → `run_simulation(...)` (same `duration`/`fold_duration`/`vibrate`/amps/`freq`) → `compute_forward_displacement`.
- Raises: `ValueError` for `duration <= 0`, invalid crease input, invalid pattern (`"invalid crease pattern: ..."` via `run_simulation`), bad trajectory; `FloatingPointError` on unstable simulation.

## `evaluate_population(...)`

```python
evaluate_population(
    individuals,                   # list of crease inputs (one per individual)
    duration=8.0,
    trajectory=(1.0, 0.0, 0.0),
    fold_duration=3.0,
    vibrate=True,
    amp_x=VIB_AMP_X, amp_z=VIB_AMP_Z, freq_hz=VIB_FREQ,
    workers=1,                     # 1 = sequential; >1 = process pool
    error_policy="raise",          # "raise" | "nan"
) -> list[float]                   # same order as `individuals`
```

- `workers=1` (or `None`): sequential loop in the current process.
- `workers>1`: `ProcessPoolExecutor` with `max_workers = min(workers, len(individuals))`; each individual is submitted as a full `evaluate_individual` run in a worker process. **Each individual costs one full simulation**, so wall time ≈ `ceil(N / workers) × duration/timestep` steps.
- `error_policy="raise"`: a failing individual raises `RuntimeError("individual {i} failed during evaluation: ...")` (wrapping the original error). `error_policy="nan"`: the slot becomes `float("nan")` and evaluation continues.
- Results preserve input order in both modes.

## Typical GA-style loop

```python
from origami_engine import evaluate_population, load_default_creases


def fitness(population):
    return evaluate_population(
        population,
        duration=4.0,
        trajectory=(1.0, 0.0, 0.0),
        fold_duration=2.0,
        workers=4,
        error_policy="nan",
    )


population = [load_default_creases() for _ in range(8)]
scores = fitness(population)
ranked = sorted(zip(scores, population), key=lambda t: t[0], reverse=True)
best_score, best_creases = ranked[0]
print(f"best: {best_score:.6f} m")
```

(Random mutation/crossover of crease lists is intentionally left to the caller — the engine only scores.)

## Practical guidance

- Keep `duration` small while iterating (e.g. 0.5–1.0 s as in `examples/01_evaluate_reference.py`); scale up for final numbers. Cost is linear in `duration` (1 ms timestep).
- Disable vibration (`vibrate=False`) when you want a deterministic, purely fold-driven score; vibration adds the dynamic "shake" effect shown in the README videos.
- Use `workers` ≈ number of physical CPU cores for `evaluate_population`; the pool pickles crease inputs, so plain lists/dicts/JSON paths are the safest individual representations.
- Compare runs with the same `duration`, `fold_duration`, `trajectory`, and vibration settings — the score is only meaningful relative to identical settings.

## See also

- [SIMULATION.md](SIMULATION.md) — what `run_simulation` does with these parameters
- [TUTORIALS.md](TUTORIALS.md) — Tutorials 3 and 6
- [API_REFERENCE.md](API_REFERENCE.md) — full signatures and raise conditions
- `origami_engine/example.py` — minimal runnable demo (`make example`)
