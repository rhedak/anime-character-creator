# The change queue during the TypeScript port

From the start of Phase 2 (2026-10-16) until cutover, the Python package is frozen (`docs/ts-port-plan.md`, section 11,
decision D10): no look changes, no new parameters, no new characters, nothing that moves `ref-out/`. The oracle the
port is measured against is the tree of tag `v0.3.0`.

Anything wanted in the meantime goes here, with the date, and is built after cutover, in TypeScript.

A **bug fix** is the one exception: it may go into Python only if it is regenerated into the manifest in the same
change (`harness/ts_port/manifest_full.py build`), recorded below, and, once the TypeScript has the code in question,
made there too in the same change. It is then released as a creator `v0.3.x` tag so the companion can pick it up.

| Date | What | Kind (idea, new look, new character, new option, bug) | Notes |
| --- | --- | --- | --- |
| | | | |
