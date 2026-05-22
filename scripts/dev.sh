#!/usr/bin/env bash
# QuBE Development Startup Script
# Usage: ./scripts/dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting QuBE development environment..."

# Check .env files
if [ ! -f "$ROOT/backend/.env" ]; then
  echo "⚠️  backend/.env not found. Copying from example..."
  cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
  echo "📝 Please edit backend/.env with your DATABASE_URL and OPENAI_API_KEY"
  exit 1
fi

if [ ! -f "$ROOT/frontend/.env.local" ]; then
  echo "📝 Creating frontend/.env.local..."
  cp "$ROOT/frontend/.env.example" "$ROOT/frontend/.env.local"
fi

# Start backend
echo "⚙️  Starting backend (FastAPI)..."
cd "$ROOT/backend"
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

# Start frontend
echo "🎨 Starting frontend (Next.js)..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ QuBE is running:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit 0" INT TERM
wait $BACKEND_PID $FRONTEND_PID
