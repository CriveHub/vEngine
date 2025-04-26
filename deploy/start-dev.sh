#!/bin/bash

IMAGE_NAME="engineproject"
IMAGE_TAG="v1.0.0"

echo "🔄 Avvio dell'ambiente di sviluppo da immagine $IMAGE_NAME:$IMAGE_TAG..."

docker-compose down

docker-compose up -d

if [ $? -eq 0 ]; then
  echo "✅ Ambiente avviato con successo."
else
  echo "❌ Errore durante l'avvio dell'ambiente." >&2
  exit 1
fi
