"""
Generate a synthetic-but-format-accurate DrGPUM memory_liveness output directory.

The byte-level formats reproduced here come from the profiler source
(`redshow/src/analysis/memory_liveness.cpp`), so the parser is exercised against
exactly the text DrGPUM emits -- including the quirks: `memory_liveness.csv`
containing non-CSV text, the trailing ", " on liveness lines, and SUBALLOC being
written with no space before its context id.

The NUMBERS are invented. This fixture exists so the pipeline is testable on a
machine with no GPU. It is not evidence of anything. Replace it with a real
capture from the remote GPU before reporting any result:

    gvprof -v -e memory_liveness ./app
    # copy the output directory to tests/fixtures/real_<appname>/

Run:  python tests/make_fixture.py
"""

from pathlib import Path

MB = 1024 * 1024

OUT = Path(__file__).parent / "fixtures" / "synthetic_run"

# op enum -- redshow/include/analysis/memory_liveness.h:110
ALLOC, SET, COPYT, COPYF, ACCESS, FREE = 0, 1, 2, 3, 4, 5

# 40 kernel launches at op_ids 100, 120, ... 880
KERNELS = list(range(100, 900, 20))

# object_id -> (size_bytes, [(op_id, op_enum), ...])
OBJECTS = {
    # healthy: allocated, filled, used early and late, freed promptly
    1000: (64 * MB, [(10, ALLOC), (12, COPYT), (100, ACCESS), (860, ACCESS), (900, FREE)]),
    # NEVER_USED: allocated and freed, never touched
    2000: (128 * MB, [(20, ALLOC), (890, FREE)]),
    # LATE_FIRST_USE: allocated at op 30, first touched at op 500
    3000: (256 * MB, [(30, ALLOC), (500, ACCESS), (700, ACCESS), (870, FREE)]),
    # DELAYED_FREE: last used at op 200, not freed until op 880
    4000: (512 * MB, [(40, ALLOC), (110, ACCESS), (200, ACCESS), (880, FREE)]),
    # NEVER_FREED: no FREE op at all
    5000: (96 * MB, [(50, ALLOC), (150, ACCESS)]),
    # REDUNDANT_H2D_COPY: two COPYT in a row with no read between
    6000: (32 * MB, [(60, ALLOC), (62, COPYT), (64, COPYT), (300, ACCESS), (850, FREE)]),
}

OP_NAME = {ALLOC: "ALLOC", SET: "SET", COPYT: "COPYT",
           COPYF: "COPYF", ACCESS: "ACCESS", FREE: "FREE"}

CURRENT_PEAK = sum(size for size, _ in OBJECTS.values())   # 1088 MB
OPTIMAL_PEAK = 384 * MB
PEAK_KERNEL = 20


def _peak_header() -> str:
    return (
        f"memory_peak_kernel: {PEAK_KERNEL}\n"
        f"optimal_memory_peak: {OPTIMAL_PEAK} B\n"
        f"current_memory_peak: {CURRENT_PEAK} B\n"
        f"\n"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # memory_liveness.txt -- output_memory_operation_list()
    #   "[<object_id>]: <op_id>(<op_enum>), ... , "  (note trailing comma-space)
    lines = []
    for object_id, (_, ops) in OBJECTS.items():
        pairs = "".join(f"{op_id}({op}), " for op_id, op in ops)
        lines.append(f"[{object_id}]: {pairs}")
    (OUT / "memory_liveness.txt").write_text("\n".join(lines) + "\n")

    # memory_size_list.txt -- output_memory_size_list(), sorted size-descending
    sized = sorted(OBJECTS.items(), key=lambda kv: kv[1][0], reverse=True)
    (OUT / "memory_size_list.txt").write_text(
        "".join(f"op_id={oid}, size={size}\n" for oid, (size, _) in sized)
    )

    # kernel_list.txt -- output_kernel_list(): "<op_id>, <ctx_id>"
    (OUT / "kernel_list.txt").write_text(
        "".join(f"{op_id}, {i + 1}\n" for i, op_id in enumerate(KERNELS))
    )

    # memory_liveness.csv -- output_ctx_node(). Despite the extension this is
    # "op_id: <n>, <OP> <ctx_id>" text, which is what caused the original
    # fictional CSV schema.
    trace = []
    for object_id, (_, ops) in OBJECTS.items():
        for op_id, op in ops:
            trace.append((op_id, OP_NAME[op], object_id))
    trace.sort()
    (OUT / "memory_liveness.csv").write_text(
        _peak_header()
        + "".join(f"op_id: {op_id}, {name} {ctx}\n" for op_id, name, ctx in trace)
    )

    # memory_growth_sequence.txt -- output_memory_size_growth_sequence()
    running, growth = 0, []
    for op_id, name, ctx in trace:
        if name == "ALLOC":
            running += OBJECTS[ctx][0]
        elif name == "FREE":
            running -= OBJECTS[ctx][0]
        growth.append(f"{op_id}({name}): {running} B\n")
    (OUT / "memory_growth_sequence.txt").write_text(_peak_header() + "".join(growth))

    print(f"wrote fixture to {OUT}")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name:<32s} {f.stat().st_size:>6d} B")


if __name__ == "__main__":
    main()
