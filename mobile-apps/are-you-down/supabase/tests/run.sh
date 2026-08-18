#!/usr/bin/env bash
#
# Apply the migrations and seed to a throwaway Postgres and assert behaviour.
#
#   npm run test:sql
#
# This is not the Supabase stack — it is a plain postgres container with the
# handful of things Supabase provides (the auth schema, auth.uid(), the anon /
# authenticated roles, the realtime publication) stubbed in bootstrap.sql. That
# is enough to exercise every policy, trigger and function we ship, and it runs
# in seconds without booting Studio, GoTrue and the rest.
#
# pg_cron isn't available here, which also exercises the migration's fallback.
set -euo pipefail

CONTAINER=ayd-sqlcheck
IMAGE=postgres:15
DB=ayd_test

HERE="$(cd "$(dirname "$0")" && pwd)"
SUPABASE_DIR="$(dirname "$HERE")"

if ! docker info >/dev/null 2>&1; then
  echo "Docker isn't running." >&2
  exit 1
fi

if ! docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "Creating $CONTAINER..."
  docker run -d --name "$CONTAINER" -e POSTGRES_PASSWORD=postgres "$IMAGE" >/dev/null
elif [ -z "$(docker ps --format '{{.Names}}' | grep -x "$CONTAINER" || true)" ]; then
  docker start "$CONTAINER" >/dev/null
fi

for _ in $(seq 1 30); do
  docker exec "$CONTAINER" pg_isready -U postgres >/dev/null 2>&1 && break
  sleep 2
done

# `docker cp <dir> <dest>` copies the directory *inside* dest when dest already
# exists, so a second run would leave /tmp/migrations/migrations and keep
# reading the first run's stale files. Clear it every time.
docker exec "$CONTAINER" rm -rf /tmp/migrations

docker cp "$HERE/bootstrap.sql"      "$CONTAINER:/tmp/bootstrap.sql" >/dev/null
docker cp "$HERE/assert.sql"         "$CONTAINER:/tmp/assert.sql"    >/dev/null
docker cp "$SUPABASE_DIR/migrations" "$CONTAINER:/tmp/migrations"    >/dev/null
docker cp "$SUPABASE_DIR/seed.sql"   "$CONTAINER:/tmp/seed.sql"      >/dev/null

run() { docker exec "$CONTAINER" psql -U postgres -d "$DB" -v ON_ERROR_STOP=1 -q "$@"; }

docker exec "$CONTAINER" psql -U postgres -q -c "drop database if exists $DB;" >/dev/null 2>&1
docker exec "$CONTAINER" psql -U postgres -q -c "create database $DB;" >/dev/null

run -f /tmp/bootstrap.sql 2>&1 | grep -Ev 'wal_level|HINT' || true

for f in $(docker exec "$CONTAINER" sh -c 'ls /tmp/migrations/*.sql | sort'); do
  run -f "$f" 2>&1 | grep -Ev 'NOTICE:.*(already exists|does not exist, skipping)' || true
done

run -f /tmp/seed.sql
run -f /tmp/assert.sql 2>&1 | grep -Ev '^\s*$|^ check|^-------|^\(1 row\)'
