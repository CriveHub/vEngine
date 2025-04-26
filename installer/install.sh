#!/usr/bin/env bash
set -e

# Plug & Play installer for EngineProject v3.5.0

# 1. Create config directory
mkdir -p /etc/engineproject
cp config/config_prod.json /etc/engineproject/config.json
cp config/jwt_key.yaml /etc/engineproject/

# 2. Build and run with Docker Compose
cp deploy/docker-compose.yml .
docker-compose pull
docker-compose up -d

echo "EngineProject v3.5.0 installed and running."
