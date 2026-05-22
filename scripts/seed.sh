#!/usr/bin/env bash
# QuBE Database Seed Script
# Usage: ./scripts/seed.sh [--fresh]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

cd "$ROOT/backend"

if [ ! -f ".env" ]; then
  echo "❌ backend/.env not found. Copy .env.example and configure it first."
  exit 1
fi

set -a
source .env
set +a

if [ "$1" == "--fresh" ]; then
  echo "⚠️  --fresh flag detected: will truncate and re-seed all data."
  FRESH="true"
else
  FRESH="false"
fi

echo "🌱 Seeding QuBE demo database..."
FRESH=$FRESH python3 -m app.db.seed.seed_main

echo ""
echo "✅ Database seeded!"
echo ""
echo "Demo credentials:"
echo "  Admin:    admin@qube.demo    / Admin123!"
echo "  Analyst:  analyst@qube.demo  / Analyst123!"
echo "  Viewer:   viewer@qube.demo   / Viewer123!"
