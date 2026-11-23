#!/usr/bin/env bash
set -euo pipefail
# GitHub-hosted disposable MariaDB service only. Never accept a remote host/database.
: "${CI_DB_HOST:?CI_DB_HOST must be explicitly configured}"
: "${CI_DB_NAME:?CI_DB_NAME must be explicitly configured}"
: "${CI_DB_USER:?CI_DB_USER must be explicitly configured}"
: "${CI_DB_PASSWORD:?CI_DB_PASSWORD must be explicitly configured}"
[[ "$CI_DB_HOST" == "127.0.0.1" ]] || { echo 'Refusing non-loopback database' >&2; exit 11; }
[[ "$CI_DB_NAME" == "public_ci_synthetic" ]] || { echo 'Refusing unexpected database name' >&2; exit 12; }
[[ "$CI_DB_USER" == "publicci" ]] || { echo 'Refusing unexpected DB user' >&2; exit 13; }
[[ "${GITHUB_ACTIONS:-}" == 'true' ]] || { echo 'Runs only in disposable GitHub Actions environment' >&2; exit 14; }

# Prefer host client against the service port mapping (reliable on GitHub-hosted runners).
# Fall back to docker exec only if a valid container ID is explicitly provided.
if [[ -n "${CI_DB_CONTAINER_ID:-}" ]]; then
  [[ "$CI_DB_CONTAINER_ID" =~ ^[0-9a-f]{64}$ ]] || { echo 'Invalid service container ID' >&2; exit 15; }
  command -v docker >/dev/null || { echo 'Disposable Docker service unavailable' >&2; exit 15; }
  service_image=$(docker inspect --format '{{.Config.Image}}' "$CI_DB_CONTAINER_ID")
  [[ "$service_image" == 'mariadb:11.4.13@sha256:9c8b5172fa219e01913060f26c5498029999657fb9b7e7bbd0ca9e87f51020e2' ]] || {
    echo 'Unexpected database service image' >&2; exit 15;
  }
  db_query() {
    docker exec -i --env "MYSQL_PWD=$CI_DB_PASSWORD" "$CI_DB_CONTAINER_ID" \
      mariadb -h 127.0.0.1 -P 3306 -u "$CI_DB_USER" --batch --skip-column-names "$CI_DB_NAME" "$@"
  }
else
  command -v mariadb >/dev/null || { echo 'mariadb client not available on host' >&2; exit 15; }
  db_query() {
    MYSQL_PWD="$CI_DB_PASSWORD" mariadb -h "$CI_DB_HOST" -P "${CI_DB_PORT:-3306}" -u "$CI_DB_USER" --batch --skip-column-names "$CI_DB_NAME" "$@"
  }
fi

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
db_query < "$root/sql/schema.sql"
db_query < "$root/sql/fixture.sql"
count=$(db_query -e 'SELECT COUNT(*) FROM ci_synthetic_items')
[[ "$count" == '3' ]] || { echo "Expected 3 synthetic rows" >&2; exit 16; }
# Connection-local transaction must roll back; query afterwards confirms count unchanged.
db_query -e "START TRANSACTION; UPDATE ci_synthetic_items SET stock=0 WHERE id=1; ROLLBACK;" >/dev/null
stock=$(db_query -e 'SELECT stock FROM ci_synthetic_items WHERE id=1')
[[ "$stock" == '14' ]] || { echo 'Rollback did not restore fixture' >&2; exit 17; }
db_query -e 'DROP TABLE ci_synthetic_items' >/dev/null
printf 'PASS: synthetic schema/fixture/rollback/drop on disposable loopback MariaDB\n'
