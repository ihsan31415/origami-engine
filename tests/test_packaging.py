"""Packaging-behavior tests: the reference pattern must ship inside the
package, and the render CLI must write outputs to the current working dir."""

import json
from pathlib import Path

import numpy as np

from origami_engine import DEFAULT_PATTERN_JSON, Crease, load_default_creases, render_individual
from origami_engine.patterns import _PACKAGED_PATTERN_JSON, _REPO_PATTERN_JSON


def test_reference_json_is_packaged_inside_the_package():
    """The wheel must contain the JSON, so installs work outside a checkout."""
    assert _PACKAGED_PATTERN_JSON.exists()
    assert _PACKAGED_PATTERN_JSON.parent.parent == Path(render_individual.__file__).resolve().parent
    assert DEFAULT_PATTERN_JSON.exists()


def test_default_creases_come_from_json_not_the_embedded_fallback():
    creases = load_default_creases()
    assert len(creases) == 24
    assert all(isinstance(c, Crease) for c in creases)
    # The loaded angles must match the packaged JSON (degrees converted to radians).
    payload = json.loads(_PACKAGED_PATTERN_JSON.read_text())
    assert len(payload["creases"]) == len(creases)
    for entry, crease in zip(payload["creases"], creases):
        assert np.isclose(crease.angle, np.radians(entry["angle"]))


def test_repo_root_copy_matches_packaged_copy():
    """In a source checkout the repo-root JSON and the packaged JSON must agree."""
    if _REPO_PATTERN_JSON.exists():
        assert _REPO_PATTERN_JSON.read_bytes() == _PACKAGED_PATTERN_JSON.read_bytes()


def test_render_outputs_resolve_to_cwd():
    """origami-render writes into the current working directory, not site-packages."""
    assert render_individual.OUTPUT_VIDEO.parent == Path.cwd()
    assert render_individual.OUTPUT_REPORT.parent == Path.cwd()
    assert render_individual.OUTPUT_VIDEO.name == "individual_simulation.mp4"
    assert render_individual.OUTPUT_REPORT.name == "render_report.json"


def test_export_video_writes_to_the_given_path(tmp_path: Path):
    frames = [np.zeros((8, 8, 3), dtype=np.uint8) for _ in range(3)]
    out = tmp_path / "clip.mp4"
    render_individual.export_video(frames, out, fps=4)
    written = out if out.exists() else out.with_suffix(".gif")  # mp4 -> gif fallback
    assert written.exists() and written.stat().st_size > 0
