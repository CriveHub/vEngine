# multi-stage Dockerfile
FROM node:16 AS builder
WORKDIR /app/frontend/reactapp
COPY src/app/frontend/reactapp/package*.json ./
RUN npm install
COPY src/app/frontend/reactapp/ .
RUN npm run build

FROM python:3.9-slim AS runtime
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=builder /app/frontend/reactapp/build /app/static
EXPOSE 5000
CMD ["python", "src/app/run_async_engine.py"]
