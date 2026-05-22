#!/usr/bin/env bash
# QuBE Database Migration Script
# Usage: ./scripts/migrate.sh [revision_message]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

cd "$ROOT/backend"

if [ ! -f ".env" ]; then
  echo "❌ backend/.env not found. Copy .env.example and configure it first."
  exit 1
fi

# Source .env for DATABASE_URL
set -a
source .env
set +a

echo "🗄️  Running Alembic migrations..."

if [ "$1" == "generate" ]; then
  MSG="${2:-auto_migration}"
  echo "📝 Generating migration: $MSG"
  python3 -m alembic revision --autogenerate -m "$MSG"
elif [ "$1" == "downgrade" ]; then
  echo "⬇️  Downgrading one step..."
  python3 -m alembic downgrade -1
elif [ "$1" == "history" ]; then
  python3 -m alembic history
elif [ "$1" == "current" ]; then
  python3 -m alembic current
else
  echo "⬆️  Applying all pending migrations..."
  python3 -m alembic upgrade head
fi

echo "✅ Migration complete."
