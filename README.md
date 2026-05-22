# QuBE — Quick Business Engine

> AI-powered Natural Language → SQL Business Intelligence platform with ticketing, dashboards, and export.

![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)

---

## Features

- **Ask Data in Plain English** — type a question, get live SQL results and an AI explanation
- **Interactive Charts** — bar, line, and pie charts auto-selected from query results
- **Auto Tickets** — every query auto-creates a support ticket with satisfaction tracking
- **Export** — download any result as CSV or formatted Excel
- **Dashboards** — KPI cards, revenue trends, appointment stats, query activity
- **Admin Tools** — schema browser, row-count overview, one-click re-seed
- **JWT Auth** — register / login / change password, role-based access (admin / analyst / viewer)

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@qube.demo` | `Admin123!` |
| Analyst | `analyst@qube.demo` | `Analyst123!` |
| Viewer | `viewer@qube.demo` | `Viewer123!` |

---

## Quick Start (Local)

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+ running locally
- OpenAI API key

### 1. Clone & configure

```bash
git clone <repo-url>
cd quick-business-engine

# Backend env
cp backend/.env.example backend/.env
# Edit backend/.env — set DATABASE_URL and OPENAI_API_KEY

# Frontend env
cp frontend/.env.example frontend/.env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Install dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 3. Run migrations

```bash
./scripts/migrate.sh
# Alternatively: cd backend && alembic upgrade head
```

### 4. Seed demo data

```bash
./scripts/seed.sh
# Use --fresh to truncate and re-seed: ./scripts/seed.sh --fresh
```

### 5. Start development servers

```bash
./scripts/dev.sh
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env — add OPENAI_API_KEY

docker compose up --build
```

Services start on:
- Frontend: http://localhost:3000
- Backend:  http://localhost:8000
- Postgres: localhost:5432

---

## Project Structure

```
quick-business-engine/
├── backend/          # FastAPI Python app
│   ├── app/
│   │   ├── ai/       # OpenAI SQL generation, validation, chart inference
│   │   ├── api/      # Route handlers (auth, queries, tickets, dashboard, admin)
│   │   ├── core/     # Config, security, exceptions, logging
│   │   ├── db/       # Database engine, seed scripts
│   │   ├── models/   # SQLAlchemy ORM models (15 tables)
│   │   ├── schemas/  # Pydantic request/response models
│   │   └── services/ # Business logic layer
│   └── alembic/      # Database migrations
├── frontend/         # Next.js 14 TypeScript app
│   ├── app/
│   │   ├── (auth)/   # Login, Register pages
│   │   └── (dashboard)/ # All protected pages
│   ├── components/   # UI components, layout, providers
│   └── lib/          # API client, auth context, utilities
├── scripts/          # dev.sh, migrate.sh, seed.sh
├── docker-compose.yml
└── plan_architecture.md
```

---

## API Overview

Base URL: `http://localhost:8000/api/v1`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Get JWT token |
| `/auth/register` | POST | Create account |
| `/queries/ask` | POST | AI NL→SQL query |
| `/queries/history` | GET | Query history |
| `/queries/{id}/export/csv` | GET | Export as CSV |
| `/queries/{id}/export/excel` | GET | Export as Excel |
| `/tickets` | GET/POST | List / create tickets |
| `/tickets/{id}/close` | POST | Close a ticket |
| `/dashboard/metrics` | GET | KPI metrics |
| `/dashboard/charts` | GET | Chart data |
| `/admin/reseed` | POST | Re-seed database |
| `/health` | GET | Health check |

Full interactive docs at `http://localhost:8000/docs`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| State | TanStack Query v5, React Context |
| Backend | FastAPI, Python 3.12, asyncio |
| ORM | SQLAlchemy 2.0 async + asyncpg |
| Migrations | Alembic |
| AI | OpenAI GPT-4o |
| Database | PostgreSQL 15 (`qube_demo` schema) |
| Auth | JWT (python-jose) + bcrypt |
| Export | openpyxl (Excel), csv |
| Deploy | Docker, Railway |

---

## Architecture

See [plan_architecture.md](plan_architecture.md) for the full architecture plan, phase breakdown, and verification checklist.
