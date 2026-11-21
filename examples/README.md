# Examples

> Part of the documentation set — traceable from the root [README.md](../README.md) via [GETTING_STARTED.md](../docs/GETTING_STARTED.md) and [TUTORIALS.md](../docs/TUTORIALS.md).

Runnable scripts showing how to use the library. Each script inserts the repository root onto `sys.path`, so they run directly from a source checkout (with the package installed editable, `pip install -e ".[dev]"` — see [GETTING_STARTED.md](../docs/GETTING_STARTED.md), Method 3):

```bash
. .venv/bin/activate
python examples/01_evaluate_reference.py
# or all of them:
make examples
```

> **Note:** the `sys.path` bootstrap means these scripts are meant to run **from a checkout**. If you installed the package from PyPI, you don't need the scripts — `import origami_engine` works anywhere, and the [tutorials](../docs/TUTORIALS.md) show the equivalent snippets.

## The scripts

| Script | What it demonstrates | Key APIs | Output |
|---|---|---|---|
| [`01_evaluate_reference.py`](01_evaluate_reference.py) | Score the reference Miura-ori pattern (fitness = forward displacement along +x) | `reference_miura_legacy_creases`, `evaluate_individual` | Prints `forward displacement: <float>` |
| [`02_json_input.py`](02_json_input.py) | Save creases to JSON and load them back (schema-validated round-trip), then evaluate the loaded pattern | `save_creases_to_json`, `load_creases_from_json`, `evaluate_individual` | Prints file size, loaded crease count/first angle, score |
| [`03_inspect_pattern.py`](03_inspect_pattern.py) | Reconstruct and inspect the face graph without simulating (no MuJoCo needed for `build_pattern`) | `build_pattern`, `load_default_creases` / `DEFAULT_PATTERN_JSON` | Prints validity, face/hinge/loop-edge counts, root face, tree depth |
| [`04_evaluate_population.py`](04_evaluate_population.py) | Score a population sequentially or with a process pool | `evaluate_population` (`workers`, `error_policy`) | Prints one score per individual |
| [`05_plot_pattern.py`](05_plot_pattern.py) | Plot the default pattern headlessly (Agg backend) and save a PNG next to the script | `plot_pattern`, `build_pattern`, `load_default_creases` | Writes `examples/05_plot_pattern.png` (gitignored) |

## How each maps to the tutorials

| Example | Tutorial in [TUTORIALS.md](../docs/TUTORIALS.md) | Deeper doc |
|---|---|---|
| 01 | Tutorial 3 — score a pattern | [EVALUATION.md](../docs/EVALUATION.md) |
| 02 | Tutorial 4 — JSON round-trip | [CREASE_FORMAT.md](../docs/CREASE_FORMAT.md) |
| 03 | Tutorial 1 — inspect a pattern | [CREASE_FORMAT.md](../docs/CREASE_FORMAT.md) |
| 04 | Tutorial 6 — population evaluation | [EVALUATION.md](../docs/EVALUATION.md) |
| 05 | Tutorial 7 — plot & save PNG | [SIMULATION.md](../docs/SIMULATION.md) (rendering) |

## Related entry points

- `make example` → `python origami_engine/example.py` — minimal `evaluate_individual` + `evaluate_population` demo.
- `make render` / `origami-render` → `origami_engine/render_individual.py` — renders the default pattern to `individual_simulation.mp4` + `render_report.json` (see [SIMULATION.md](../docs/SIMULATION.md)).

## See also

- [GETTING_STARTED.md](../docs/GETTING_STARTED.md) — installation methods
- [TUTORIALS.md](../docs/TUTORIALS.md) — nine step-by-step recipes
- [API_REFERENCE.md](../docs/API_REFERENCE.md) — full API signatures
