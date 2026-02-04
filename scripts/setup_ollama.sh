#!/usr/bin/env bash
# Setup Ollama for local LLM: install (instructions), start service, pull model.
# Run from project root: ./scripts/setup_ollama.sh

set -e

OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2}"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

echo "--- Ollama setup (local LLM) ---"

if ! command -v ollama &>/dev/null; then
  echo "Ollama is not installed."
  echo ""
  echo "Install it first:"
  echo "  macOS (Homebrew):  brew install ollama"
  echo "  If brew says 'not writable', fix permissions then retry:"
  echo "    sudo chown -R \$(whoami) /opt/homebrew /opt/homebrew/Cellar"
  echo "  Or download the app: https://ollama.com/download"
  echo ""
  exit 1
fi

echo "Ollama found: $(ollama --version 2>/dev/null || ollama version 2>/dev/null || true)"

# Start Ollama in background if not already responding
if ! curl -s -o /dev/null -w "%{http_code}" "$OLLAMA_URL/api/tags" 2>/dev/null | grep -q 200; then
  echo "Starting Ollama service in background..."
  ollama serve &
  OLLAMA_PID=$!
  sleep 3
  if ! kill -0 $OLLAMA_PID 2>/dev/null; then
    echo "Ollama may already be running. Continuing."
  fi
else
  echo "Ollama is already running at $OLLAMA_URL"
fi

# Wait for Ollama to be ready
for i in {1..10}; do
  if curl -s -o /dev/null "$OLLAMA_URL/api/tags" 2>/dev/null; then
    break
  fi
  echo "Waiting for Ollama... ($i/10)"
  sleep 2
done

if ! curl -s -o /dev/null "$OLLAMA_URL/api/tags" 2>/dev/null; then
  echo "Ollama did not become ready. Start it manually: ollama serve"
  exit 1
fi

echo "Pulling model: $OLLAMA_MODEL (this may take a few minutes)"
ollama pull "$OLLAMA_MODEL"

echo ""
echo "Ollama is ready. Ensure .env has:"
echo "  LLM_PROVIDER=ollama"
echo "  OLLAMA_MODEL=$OLLAMA_MODEL"
echo "  OLLAMA_BASE_URL=$OLLAMA_URL/v1"
echo ""
echo "Then start the backend and run the test:"
echo "  Terminal 1: uvicorn backend.main:app --reload"
echo "  Terminal 2: python scripts/terminal_test.py"
echo ""
