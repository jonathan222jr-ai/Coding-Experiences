"""
Tests for the DrGPUM memory_liveness parser and detectors.

Runs without a GPU: everything is exercised against the format-accurate fixture
in `fixtures/synthetic_run` (regenerate with `python tests/make_fixture.py`).

    python -m pytest tests/ -v
"""

from pathlib import Path

import pytest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.drgpum import DrGPUMParseError, analyze, parse_profile  # noqa: E402
from agent.drgpum.detectors import (  # noqa: E402
    detect_delayed_free,
    detect_late_first_use,
    detect_never_freed,
    detect_never_used,
    detect_peak_gap,
    detect_redundant_h2d,
)

MB = 1024 * 1024
FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_run"


@pytest.fixture(scope="module")
def profile():
    return parse_profile(FIXTURE)


# -- parsing ----------------------------------------------------------------

def test_parses_all_objects(profile):
    assert set(profile.objects) == {1000, 2000, 3000, 4000, 5000, 6000}


def test_parses_sizes(profile):
    assert profile.objects[4000].size_bytes == 512 * MB
    assert profile.objects[6000].size_bytes == 32 * MB


def test_parses_op_sequence_with_enum_names(profile):
    ops = [(o.op_id, o.op) for o in profile.objects[6000].ops]
    assert ops == [
        (60, "ALLOC"),
        (62, "COPYT"),
        (64, "COPYT"),
        (300, "ACCESS"),
        (850, "FREE"),
    ]


def test_parses_kernel_list(profile):
    assert len(profile.kernel_ops) == 40
    assert profile.kernel_op_ids[0] == 100
    assert profile.kernel_op_ids[-1] == 880


def test_parses_peak_header_from_non_csv_csv(profile):
    # memory_liveness.csv carries a .csv extension but holds text; the peak
    # summary must still be read out of it.
    assert profile.current_memory_peak == 1088 * MB
    assert profile.optimal_memory_peak == 384 * MB
    assert profile.memory_peak_kernel == 20


def test_peak_gap(profile):
    assert profile.peak_gap_bytes == (1088 - 384) * MB
    assert profile.peak_waste_fraction == pytest.approx(704 / 1088)


def test_kernels_between_counts_launches_not_op_ids(profile):
    # kernels are at 100,120,...,880
    assert profile.kernels_between(100, 200) == 4     # 120,140,160,180
    assert profile.kernels_between(200, 100) == 0     # inverted range
    assert profile.kernels_between(0, 10_000) == 40


def test_rejects_non_drgpum_directory(tmp_path):
    (tmp_path / "profile.csv").write_text("kernel_name,runtime_ms\nfoo,1.0\n")
    with pytest.raises(DrGPUMParseError, match="memory_liveness.txt not found"):
        parse_profile(tmp_path)


def test_accepts_a_file_inside_the_directory(profile):
    # convenience: pointing at a file resolves to its parent directory
    p = parse_profile(FIXTURE / "memory_liveness.txt")
    assert set(p.objects) == set(profile.objects)


# -- object-level properties ------------------------------------------------

def test_never_used_object_has_no_use_ops(profile):
    assert profile.objects[2000].is_never_used
    assert not profile.objects[1000].is_never_used


def test_never_freed_detected_on_object(profile):
    assert profile.objects[5000].is_never_freed
    assert not profile.objects[4000].is_never_freed


def test_first_and_last_use(profile):
    obj = profile.objects[3000]
    assert obj.alloc_op == 30
    assert obj.first_use_op == 500
    assert obj.last_use_op == 700


# -- detectors --------------------------------------------------------------

def test_detect_never_used(profile):
    found = detect_never_used(profile)
    assert [f.object_id for f in found] == [2000]
    assert found[0].size_bytes == 128 * MB


def test_detect_late_first_use(profile):
    found = detect_late_first_use(profile)
    assert [f.object_id for f in found] == [3000]
    # allocated at op 30, first used at op 500 -> kernels at 100..480 = 20
    assert found[0].idle_kernels == 20
    assert found[0].idle_byte_kernels == 256 * MB * 20


def test_detect_delayed_free(profile):
    found = {f.object_id: f for f in detect_delayed_free(profile)}
    # An object can exhibit more than one inefficiency at once, and real
    # profiles are full of such overlap -- 3000 is both a LATE_FIRST_USE and a
    # DELAYED_FREE. Detectors are deliberately independent; ranking, not
    # suppression, is what separates them.
    assert set(found) == {3000, 4000, 6000}
    # 4000: last used at op 200, freed at op 880 -> kernels 220..860 = 33
    assert found[4000].idle_kernels == 33
    # 3000: last used at op 700, freed at op 870 -> kernels 720..860 = 8
    assert found[3000].idle_kernels == 8


def test_object_can_carry_multiple_finding_kinds(profile):
    kinds = {f.kind for f in analyze(profile) if f.object_id == 3000}
    assert {"LATE_FIRST_USE", "DELAYED_FREE"} <= kinds


def test_detect_never_freed(profile):
    found = detect_never_freed(profile)
    assert [f.object_id for f in found] == [5000]


def test_detect_redundant_h2d(profile):
    found = detect_redundant_h2d(profile)
    assert [f.object_id for f in found] == [6000]
    assert found[0].detail["redundant_transfers"] == 1


def test_healthy_object_produces_no_findings(profile):
    ids = {f.object_id for f in analyze(profile)}
    assert 1000 not in ids


def test_peak_gap_is_reported(profile):
    found = detect_peak_gap(profile)
    assert len(found) == 1
    assert found[0].size_bytes == 704 * MB
    assert found[0].object_id is None


def test_min_bytes_threshold_filters_small_objects(profile):
    assert analyze(profile, min_bytes=1024 * MB) == [] or all(
        f.object_id is None for f in analyze(profile, min_bytes=1024 * MB)
    )


def test_min_idle_kernels_threshold(profile):
    assert detect_delayed_free(profile, min_idle_kernels=100) == []


def test_findings_ranked_by_severity(profile):
    sev = [f.severity for f in analyze(profile)]
    assert sev == sorted(sev, reverse=True)


def test_every_finding_answers_all_three_questions(profile):
    # The professor's rubric: what, why harmful, how to fix.
    for f in analyze(profile):
        assert f.evidence.strip(), f"{f.kind} has no evidence"
        assert f.harm.strip(), f"{f.kind} has no harm statement"
        assert f.fix.strip(), f"{f.kind} has no fix"
        assert f.to_dict()["size_human"]


# ---------------------------------------------------------------------------
# Real profiler output.
#
# Captured on an RTX 3090 from the upstream vectorAdd.f32 sample:
#     gvprof -v -e memory_liveness ./vectorAdd
# Tiny (3 objects, 1 kernel, 4 B each) but REAL -- these assertions are what
# prove the formats were derived correctly rather than plausibly.
# ---------------------------------------------------------------------------

REAL = Path(__file__).parent / "fixtures" / "real_vectoradd"

pytestmark_real = pytest.mark.skipif(
    not (REAL / "memory_liveness.txt").is_file(), reason="real fixture not present"
)


@pytest.fixture(scope="module")
def real():
    return parse_profile(REAL)


@pytestmark_real
def test_real_profile_parses(real):
    assert len(real.objects) == 3
    assert len(real.kernel_ops) == 1


@pytestmark_real
def test_real_op_ids_exceed_64bit_signed_range(real):
    # DrGPUM seeds op_ids at 2**63 + n. Anything storing these as int64 breaks.
    assert min(real.objects) > 2**63


@pytestmark_real
def test_real_op_sequence(real):
    obj = real.objects[min(real.objects)]
    assert [o.op for o in obj.ops] == ["ALLOC", "COPYT", "FREE"]
    assert obj.size_bytes == 4


@pytestmark_real
def test_real_peak_underflow_is_unwrapped(real):
    # The file literally contains current_memory_peak: 18446744073709551116,
    # which is (12 - 512) wrapped to unsigned 64-bit by output_ctx_node().
    assert real.peak_underflowed is True
    assert real.current_memory_peak == 12  # agrees with memory_growth_sequence


@pytestmark_real
def test_real_peak_gap_suppressed_on_underflowed_run(real):
    assert detect_peak_gap(real) == []


@pytestmark_real
def test_real_call_stack_attribution(real):
    obj = real.objects[min(real.objects)]
    stack = real.call_stack_for(obj)
    assert stack, "no call stack -- memory_liveness.csv.context not joined"
    assert any("cudaMalloc" in f for f in stack)
    assert any("main" in f for f in stack)


# ---------------------------------------------------------------------------
# Fully-instrumented PyTorch capture (torch-monitor + on-GPU liveness).
#
#   gvprof -v -ck HPCRUN_SANITIZER_LIVENESS_ONGPU=1 \
#             -ck HPCRUN_SANITIZER_TORCH_ANALYSIS=1 \
#             -e memory_liveness python3 train_small.py
#
# Both knobs are off by default in DrGPUM and both are required. Captured on an
# RTX 3090, torch 2.6.0+cu124.
# ---------------------------------------------------------------------------

FULL = Path(__file__).parent / "fixtures" / "real_pytorch_full"

needs_full = pytest.mark.skipif(
    not (FULL / "submemory_liveness.txt").is_file(), reason="full fixture not present"
)


@pytest.fixture(scope="module")
def full():
    return parse_profile(FULL)


@needs_full
def test_submemory_parsed(full):
    # 180 tensors sub-allocated inside 11 allocator segments
    assert len(full.submemory) == 180
    assert len(full.objects) == 11
    assert full.has_submemory


@needs_full
def test_access_tracking_detected(full):
    # LIVENESS_ONGPU=1 was set, so ACCESS ops exist at segment level
    assert full.access_tracking_available


@needs_full
def test_optimal_peak_is_computed_with_ongpu_knob(full):
    # Without LIVENESS_ONGPU this is 0 and peak_gap_bytes is None.
    assert full.optimal_peak_available
    assert full.optimal_memory_peak == 46137344      # 44.0 MB
    assert full.current_memory_peak == 65275392      # 62.3 MB
    assert full.peak_gap_bytes == 19138048           # 18.3 MB recoverable


@needs_full
def test_python_attribution_reaches_application_source(full):
    # The point of torch-monitor: an object id becomes a source line.
    sites = [
        full.python_site(o.alloc_op)
        for o in full.submemory.values()
        if o.alloc_op is not None
    ]
    app = [s for s in sites if s is not None and s.is_application]
    assert app, "no application frames resolved"
    assert any("train_small.py" in s.file for s in app)
    # every application frame carries a usable line number
    assert all(s.call_line > 0 for s in app)


@needs_full
def test_python_frame_skips_torch_internals(full):
    from agent.drgpum.parser import PythonFrame

    internal = PythonFrame("/x/site-packages/torch/nn/modules/module.py", "to", 1, 2)
    app = PythonFrame("/home/u/train.py", "<module>", 1, 25)
    assert not internal.is_application
    assert app.is_application


@needs_full
def test_submemory_view_runs_detectors_at_tensor_granularity(full):
    view = full.submemory_view()
    assert len(view.objects) == 180
    assert view.current_memory_peak == full.current_submemory_peak
    # ACCESS is attributed to the parent segment, never the tensor, so
    # usage-based detection must stay suppressed on the tensor view.
    assert not view.access_tracking_available
    assert detect_never_used(view) == []


@needs_full
def test_never_used_suppressed_without_access_data():
    # A profile with no ACCESS anywhere must not report every object unused.
    p = parse_profile(FIXTURE)  # synthetic fixture has ACCESS
    assert p.access_tracking_available
    for obj in p.objects.values():
        obj.ops = [o for o in obj.ops if o.op != "ACCESS"]
    assert not p.access_tracking_available
    assert detect_never_used(p) == []
