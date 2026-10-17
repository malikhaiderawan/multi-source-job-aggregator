#!/bin/bash

# Function to gracefully kill all background processes on exit (Ctrl+C)
cleanup() {
  echo ""
  echo "🛑 Stopping backend and frontend servers..."
  kill $(jobs -p) 2>/dev/null
  exit
}

trap cleanup EXIT INT TERM

echo "🚀 Starting Job Integration Gateway (Full-Stack)..."

# 0. Check for .env file
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
  fi
fi

# 1. Setup & start Python Backend
if [ ! -d ".venv" ]; then
  echo "📦 Creating Python virtual environment (.venv)..."
  python3 -m venv .venv
  echo "📥 Installing backend requirements..."
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
fi

echo "🟢 Launching FastAPI Backend on http://localhost:8000..."
.venv/bin/python main.py &

# 2. Setup & start Next.js Frontend
cd frontend

if [ ! -d "node_modules" ]; then
  echo "📦 Installing frontend npm dependencies..."
  npm install
fi

echo "🟢 Launching Next.js Frontend on http://localhost:3000..."
npm run dev