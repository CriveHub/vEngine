#!/bin/bash

# Nome immagine e tag
IMAGE_NAME="engineproject"
IMAGE_TAG="v1.0.0"

# Percorso della directory del progetto
# PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
read -p "📂 Inserisci il percorso della directory contenente il Dockerfile: " PROJECT_DIR
if [ ! -f "$PROJECT_DIR/Dockerfile" ]; then
  echo "❌ Dockerfile non trovato in: $PROJECT_DIR" >&2
  exit 1
fi

echo "Building Docker image: $IMAGE_NAME:$IMAGE_TAG"
docker build -t "$IMAGE_NAME:$IMAGE_TAG" "$PROJECT_DIR"

if [ $? -eq 0 ]; then
  echo "✅ Image $IMAGE_NAME:$IMAGE_TAG built successfully."
else
  echo "❌ Failed to build the image." >&2
  exit 1
fi
