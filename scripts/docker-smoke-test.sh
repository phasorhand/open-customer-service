#!/usr/bin/env bash
# Smoke-test the full Docker compose stack.
#
# Usage:
#   ./scripts/docker-smoke-test.sh
#
# Assumes `docker compose up -d --build` has already been run.
set -euo pipefail

echo "== Waiting for opencs-api =="
for i in $(seq 1 30); do
  if curl -fsS http://localhost:8000/health > /dev/null 2>&1; then
    echo "opencs-api healthy"
    break
  fi
  sleep 2
done
curl -fsS http://localhost:8000/health
echo

echo "== Waiting for web-ui =="
for i in $(seq 1 30); do
  if curl -fsS -o /dev/null http://localhost:3000/; then
    echo "web-ui healthy"
    break
  fi
  sleep 2
done

echo "== Waiting for langfuse =="
for i in $(seq 1 60); do
  if curl -fsS -o /dev/null http://localhost:3001/api/public/health; then
    echo "langfuse healthy"
    break
  fi
  sleep 2
done

echo "== Checking admin proposals endpoint =="
RESP=$(curl -fsS http://localhost:8000/admin/proposals)
echo "admin/proposals response: $RESP"
echo "$RESP" | grep -q '"total"' || { echo "admin endpoint response unexpected"; exit 1; }

echo "== Checking web-ui proxies to api =="
RESP=$(curl -fsS http://localhost:3000/api/admin/proposals)
echo "web /api/admin/proposals response: $RESP"
echo "$RESP" | grep -q '"total"' || { echo "web proxy failed"; exit 1; }

echo "== All smoke checks passed =="
