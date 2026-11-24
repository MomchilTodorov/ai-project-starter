FROM node:26-bookworm-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-bookworm
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ai_client.py app.py database.py policy_demo.py production.py product_tools.py store_policies.py ./
COPY --from=frontend-build /build/dist ./frontend/dist

EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn production:app --host 0.0.0.0 --port \"${PORT:-8000}\""]