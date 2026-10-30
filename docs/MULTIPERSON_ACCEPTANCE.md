# Multi-person acceptance plan

The software contract permits up to three people, but multi-person tracking is
not implemented. Do not enable multi-person claims based on this scaffold.

Before M6/M7 release, test person counts 0→1→2→3→2→1→0, detector result
reordering, side-by-side movement, crossing, partial/full occlusion, exit and
re-entry, per-track filter isolation, stale packets, and loss/recovery behavior.
An uncertain identity must freeze/fade or reassign visibly rather than silently
transfer one person's motion to another skeleton. Record measured conditions,
FPS, coverage, ID switches, recovery, and latency; mark absent tests
`NOT_TESTED`.
