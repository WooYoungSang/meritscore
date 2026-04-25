#!/bin/bash
# Emergency fallback: local Streamlit + ngrok tunnel
# Usage: ./scripts/fallback_demo.sh
#
# This script starts the local BFF (FastAPI), Streamlit UI, and ngrok tunnel
# for demo resilience in case the deployed server is unavailable.
#
# Prerequisites:
# - ngrok installed (brew install ngrok)
# - ngrok authtoken configured (ngrok config add-authtoken <token>)
# - Python deps installed (pip install -r app/requirements.txt)
# - FastAPI/uvicorn available

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Emergency Demo Fallback"
echo "=========================================="
echo ""
echo "Starting local services..."
echo ""

# Trap to kill all child processes on exit
cleanup() {
    echo ""
    echo "=========================================="
    echo "Shutting down services..."
    echo "=========================================="
    kill $BFF_PID $STREAMLIT_PID $NGROK_PID 2>/dev/null || true
    wait 2>/dev/null || true
    echo "All services stopped."
}
trap cleanup EXIT

# 1. Start local BFF (FastAPI) on port 61234
echo "[1/3] Starting BFF (FastAPI) on port 61234..."
python -m uvicorn python.bff.main:app \
    --host 0.0.0.0 \
    --port 61234 \
    --reload &
BFF_PID=$!
echo "      BFF PID: $BFF_PID"

# 2. Start Streamlit UI on port 8501
echo "[2/3] Starting Streamlit UI on port 8501..."
streamlit run app/main.py \
    --server.port 8501 \
    --server.headless true \
    --logger.level=error &
STREAMLIT_PID=$!
echo "      Streamlit PID: $STREAMLIT_PID"

# 3. Start ngrok tunnel for BFF
echo "[3/3] Starting ngrok tunnel for BFF..."
ngrok http 61234 --log=stdout &
NGROK_PID=$!
echo "      ngrok PID: $NGROK_PID"

echo ""
echo "=========================================="
echo "✅ All services started!"
echo "=========================================="
echo ""
echo "📱 Streamlit URL:"
echo "   http://localhost:8501"
echo ""
echo "🌐 ngrok BFF Tunnel:"
echo "   Check http://localhost:4040 for live public URL"
echo "   (or view ngrok CLI output below)"
echo ""
echo "📊 Local BFF (FastAPI):"
echo "   http://localhost:61234"
echo "   Swagger UI: http://localhost:61234/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# Wait for all background processes
wait
