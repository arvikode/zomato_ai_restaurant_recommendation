#!/bin/bash
# Validation script - run from project root
# Usage: ./validate.sh  (or: bash validate.sh)

set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "  AI Restaurant Recommender - Validation"
echo "=========================================="
echo ""

# 1. Ensure .env exists (app loads .env, NOT .env.example)
if [ ! -f .env ]; then
  echo "Copying .env.example to .env (app reads .env only)"
  cp .env.example .env
  echo "  -> Edit .env with GROK_API_KEY (for recommendations)"
else
  echo "Using existing .env (if you updated .env.example, run: cp .env.example .env)"
fi
echo ""

# 2. Unit tests
echo "[1/4] Running unit tests..."
python -m pytest tests/ -v --tb=short -q 2>/dev/null || python run_tests.py
echo "  -> Unit tests passed"
echo ""

# 3. Database: SQLite by default
echo "[2/4] Database: SQLite (data/restaurants.db) - no setup"
echo ""

# 4. Check GROK_API_KEY
echo "[3/4] Checking GROK_API_KEY..."
if grep -q "GROK_API_KEY=.\+" .env 2>/dev/null && ! grep -q "GROK_API_KEY=dummy-key-replace-me" .env 2>/dev/null; then
  echo "  -> GROK_API_KEY is set (not dummy)"
else
  echo "  -> WARNING: GROK_API_KEY is empty or still dummy (POST /recommendations will return 503)"
fi
echo ""

# 5. Quick API smoke test (start server, hit endpoints, stop)
echo "[4/4] API smoke test..."
if ! command -v uvicorn &>/dev/null; then
  echo "  -> Skipped (uvicorn not found)"
else
  echo "  Starting server..."
  uvicorn backend.main:app --host 127.0.0.1 --port 8000 2>/dev/null &
  SERVER_PID=$!
  sleep 3
  trap "kill $SERVER_PID 2>/dev/null" EXIT

  curl -s http://127.0.0.1:8000/ | grep -q "ok" && echo "  -> GET / OK" || echo "  -> GET / failed"
  CITIES=$(curl -s http://127.0.0.1:8000/cities 2>/dev/null || echo "[]")
  echo "$CITIES" | grep -q "\[" && echo "  -> GET /cities OK" || echo "  -> GET /cities: $CITIES"
  REC=$(curl -s -X POST http://127.0.0.1:8000/recommendations -H "Content-Type: application/json" -d '{"city":"Bangalore","price_category":"$$","limit":3}' 2>/dev/null || echo "{}")
  echo "$REC" | grep -q "recommendations" && echo "  -> POST /recommendations OK" || echo "  -> POST /recommendations: ${REC:0:60}..."
fi

echo ""
echo "=========================================="
echo "  Validation complete"
echo "=========================================="
echo ""
echo "Manual test commands:"
echo "  1. Start server:  uvicorn backend.main:app --reload"
echo "     (Data auto-loads from HuggingFace on first start, ~1-2 min)"
echo "  2. Re-ingest:     python scripts/ingest_zomato_data.py"
echo "  3. Swagger UI:    open http://localhost:8000/docs"
echo "  4. Test cities:   curl http://localhost:8000/cities"
echo '  5. Test recommend: curl -X POST http://localhost:8000/recommendations \'
echo '       -H "Content-Type: application/json" -d '\''{"city":"Bangalore","price_category":"$$","limit":3}'\'''
echo ""
