#!/bin/bash

# Function to kill background jobs on exit
cleanup() {
    echo "Stopping TeleGuard Services..."
    kill $(jobs -p)
    exit
}

# Set up trap for cleanup
trap cleanup EXIT

echo "🚀 Starting TeleGuard Core Services..."

# Start Backend
echo "[1/2] Launching API Server (Uvicorn)..."
./venv/bin/uvicorn app.main:app --reload &
BACKEND_PID=$!

# Start Worker
echo "[2/2] Launching Background Worker..."
./venv/bin/python worker.py &
WORKER_PID=$!

echo "✅ Services Running!"
echo "   - Backend: http://127.0.0.1:8000"
echo "   - Worker:  Active (PID: $WORKER_PID)"
echo ""
echo "Press Ctrl+C to stop both."

# Wait for both processes
wait
