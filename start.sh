#!/usr/bin/env bash
set -e
# Builds frontend if missing, then runs gunicorn
cd "$(dirname "$0")"
if [ ! -d "frontend/build" ]; then
  if command -v npm >/dev/null 2>&1; then
    echo "Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
  else
    echo "Warning: npm not found. Please install Node/npm and run 'cd frontend && npm install && npm run build'." >&2
  fi
fi

echo "Starting gunicorn..."
exec gunicorn app:app
