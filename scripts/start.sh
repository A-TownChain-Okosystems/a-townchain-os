#!/bin/bash
# A-TownChain Monorepo — Start Script
# K2 Konsolidierung

set -e

echo "=== A-TownChain Start ==="

# Start all services via Docker Compose
docker-compose -f docker/docker-compose.yml up -d

echo "=== Services started ==="
echo "  Core:       http://localhost:8000"
echo "  Frontend:    http://localhost:3000"
echo "  Gateway:     http://localhost:80"
echo "  Blockchain:  http://localhost:8545"
echo "  Monitoring:  http://localhost:9090"
