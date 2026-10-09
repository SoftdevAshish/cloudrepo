#!/usr/bin/env bash
# Boots the API on a throwaway SQLite file and exercises auth + authorization end to end.
# Usage: scripts/smoke.sh   (from the repo root, with dependencies installed)
set -euo pipefail
PORT=${PORT:-8765}; DB=$(mktemp -u /tmp/smoke-XXXXXX.db); B=http://localhost:$PORT/api/v1
export DB_NAME=$DB CELERY_TASK_ALWAYS_EAGER=true CELERY_RESULT_BACKEND=cache+memory:// \
  CELERY_BROKER_URL=memory:// ADMIN_EMAIL=root@example.com ADMIN_PASSWORD=root-password-1 BCRYPT_ROUNDS=4
uvicorn app.main:app --port "$PORT" >/tmp/smoke-uvicorn.log 2>&1 &
PID=$!; trap 'kill $PID 2>/dev/null; rm -f "$DB"' EXIT
for _ in $(seq 20); do curl -sf "http://localhost:$PORT/health" >/dev/null && break; sleep 0.5; done
j() { curl -s "$@"; }; H='content-type: application/json'
tok() { j -X POST "$B/auth/login" -H "$H" -d "{\"email\":\"$1\",\"password\":\"$2\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])'; }
j -X POST "$B/auth/register" -H "$H" -d '{"email":"u@example.com","password":"password-123"}' >/dev/null
U=$(tok u@example.com password-123); A=$(tok root@example.com root-password-1)
j -X POST "$B/todos" -H "authorization: Bearer $U" -H "$H" -d '{"title":"hello"}' >/dev/null
check() { [ "$2" = "$3" ] && echo "ok   $1" || { echo "FAIL $1 (got $2, want $3)"; exit 1; }; }
check "user lists own todo"   "$(j "$B/todos" -H "authorization: Bearer $U" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))')" 1
check "user -> /databases"    "$(j -o /dev/null -w '%{http_code}' "$B/databases" -H "authorization: Bearer $U")" 403
check "admin -> /databases"   "$(j -o /dev/null -w '%{http_code}' "$B/databases" -H "authorization: Bearer $A")" 200
check "no token"              "$(j -o /dev/null -w '%{http_code}' "$B/todos")" 401
check "admin lists roles"     "$(j "$B/roles" -H "authorization: Bearer $A" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))')" 2
echo "smoke test passed"
