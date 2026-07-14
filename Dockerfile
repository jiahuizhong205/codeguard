# Frontend build stage
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Backend build stage
FROM python:3.12-slim AS backend-builder
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
COPY tests/ ./tests/
RUN pip install --no-cache-dir -e ".[dev]"

# Runtime stage
FROM python:3.12-slim
WORKDIR /app
COPY --from=backend-builder /app /app
COPY --from=frontend-builder /frontend/dist /app/src/codeguard/static
RUN useradd -m codeguard && chown -R codeguard:codeguard /app
USER codeguard
EXPOSE 8000
CMD ["python", "-m", "codeguard", "serve"]
