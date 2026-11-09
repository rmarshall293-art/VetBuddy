# ADR 0002 — Runtime stack for slice 01

**Status:** Accepted, temporary. Revisit when package registries are reachable.

**Context.** The build environment blocked pip and npm (egress proxy 403). Preinstalled: Python 3.13, Starlette 1.7, Pydantic 2.13, uvicorn, libpq, Playwright/Chromium. Missing: FastAPI, psycopg, pytest, Vite/React. No Base44 Vite export was supplied, so there was no working UI to preserve.

**Decision.**
- **API:** Starlette + Pydantic v2. FastAPI is a layer over exactly these, and route handlers keep FastAPI's shape (typed request models, a single principal resolver), so migrating means rewriting `app/api/v1.py` and nothing else.
- **DB driver:** a minimal libpq binding (`app/infra/db.py`, about 200 lines) using `PQexecParams` with out-of-band parameters only. Swapping in psycopg 3 changes only this file.
- **Tests:** stdlib `unittest`. pytest discovers these unchanged.
- **Web:** framework-free ES modules with no build step, the same approach as the Sentinel prototype. Built with an `el()` DOM helper (no `innerHTML` with data) and a strict CSP.

**When to revisit.** Once the Base44 Vite export is available, the master spec says to preserve it. This shell's screens (onboarding, brief, tasks, privacy, help) then become reference behavior, with `smoke_ui.py` as the acceptance test. A move to Next.js needs its own ADR.
