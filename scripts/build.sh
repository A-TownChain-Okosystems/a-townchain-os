#!/bin/bash
# A-TownChain Monorepo — Build Script
# K2 Konsolidierung

set -e

echo "=== A-TownChain Build ==="

# Python Backend
echo "[1/3] Installing Python dependencies..."
pip install -r requirements.txt

# Frontend
echo "[2/3] Building Frontend..."
cd frontend && npm ci && npm run build && cd ..

# Docker
echo "[3/3] Building Docker images..."
docker-compose -f docker/docker-compose.yml build

echo "=== Build complete ==="
