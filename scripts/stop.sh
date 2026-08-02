#!/bin/bash
# A-TownChain Monorepo — Stop Script
# K2 Konsolidierung

echo "=== A-TownChain Stop ==="
docker-compose -f docker/docker-compose.yml down
echo "=== Services stopped ==="
