# VetBuddy (Supabase + FastAPI)

VetBuddy is a unified veteran support platform built on a modern stack:
- Frontend: React + Vite
- Backend: FastAPI
- Database/Auth/Storage: Supabase (Postgres)

## Quick Start

### 1. Clone Repo
```bash
git clone https://github.com/rmarshall293-art/VetBuddy.git
cd VetBuddy
```

### 2. Setup Environment
Create `.env` files based on examples in:
- frontend/.env.example
- backend/.env.example

### 3. Run Locally (Docker)
```bash
docker-compose up --build
```

Frontend: http://localhost:5173  
Backend: http://localhost:8000

### 4. Supabase Setup
- Create a project at https://supabase.com
- Run `supabase/schema.sql`
- Copy keys into `.env`

## Architecture
- `frontend/` UI + API client
- `backend/` FastAPI API (compat + domain routes)
- `supabase/` schema + RLS policies
- `data/` datasets
- `docs/` migration + hardening docs

## Deployment
- Frontend → Vercel / Netlify
- Backend → Railway / Render / Fly.io
- Database/Auth → Supabase

## Status
Production-ready baseline with compatibility layer. Next step: convert compatibility endpoints to fully typed domain services.

## License
Private / Internal Use
