#!/bin/bash
# Deploys origin/main. CI runs it over SSH as the forced command of its deploy key,
# so that key can do nothing else on the server. Safe to run by hand too.
set -euo pipefail

# Wrapped in a function: bash reads scripts lazily, and `git reset` may rewrite this file.
main() {
  cd "$(dirname "$0")/.."
  git fetch --quiet origin main
  git reset --hard origin/main  # .env is untracked, so it survives
  cd deploy
  docker compose up -d --build --remove-orphans
  docker image prune -f >/dev/null

  # The app checks Host and redirects plain HTTP, so ask the way nginx does.
  local host
  host=$(grep '^DJANGO_ALLOWED_HOSTS=' .env | cut -d= -f2 | cut -d, -f1)
  for _ in $(seq 30); do
    code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: $host" \
      -H 'X-Forwarded-Proto: https' http://127.0.0.1:18082/api/health || true)
    if [ "$code" = 200 ]; then echo "deployed $(git rev-parse --short HEAD)"; return 0; fi
    sleep 2
  done
  echo "health check failed (last status: $code)" >&2
  docker compose logs --tail=30 app >&2
  return 1
}
main "$@"
exit
