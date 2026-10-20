# ADR 0002: Web UI stack — Vite, no framework yet

Status: Accepted, 20 Oct 2026

## Context
The project rule is "prefer the existing working Vite UI; adopt Next.js only after an ADR". No Base44 React source is available. The one working UI we have is the guest app (`vetbuddy.html`): plain ES modules, no framework, already accessible and privacy-tested.

## Decision
Keep that app as-is inside a Vite project (`frontend/`). Split into `kernel.js` (pure logic), `kernel_data.js` (generated from Python by `scripts/build_web.py`), `main.js` (guest views) and `plan.js` (saved plan, present only when `VITE_API_URL` is set). No React/Next.js rewrite now.

## Consequences
- Guest build (no `VITE_API_URL`) has no backend and is the Launch 0 shape; its CSP allows network only to its own origin.
- When the Base44 React export arrives, its screens can be brought in under Vite with React added then; that is a deliberate migration with its own ADR, not a silent rewrite.
- Browser and server answers are kept identical by the parity test rather than by sharing code.
