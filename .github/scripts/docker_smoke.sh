#!/usr/bin/env bash
# Smoke test for a built mcp-mixsearch image. Run by .github/workflows/docker-publish.yml before
# any push, and locally: .github/scripts/docker_smoke.sh <image>
# Set EXPECTED_REVISION to a commit SHA to also check the image's revision label.
#
# Checks, failing on the first problem:
#   1. The revision label is EXPECTED_REVISION (when set).
#   2. Playwright in the image is the version uv.lock locks, and it launches headless Firefox.
#   3. `--help` prints the server's usage and exits 0.
#   4. The server starts with no network and answers /health (on 3000, and on 3001 via --port),
#      and answers through a published port from the host.
#   5. /health reports the version in pyproject.toml.
set -euo pipefail

image="${1:?usage: docker_smoke.sh <image>}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
timeout_s="${SMOKE_TIMEOUT_SECONDS:-60}"
containers=()

cleanup() {
  for c in "${containers[@]}"; do docker rm -f "$c" >/dev/null 2>&1 || true; done
}
trap cleanup EXIT

fail() {
  echo "smoke test FAILED: $*" >&2
  for c in "${containers[@]}"; do
    echo "--- docker logs $c ---" >&2
    docker logs "$c" >&2 2>&1 || true
  done
  exit 1
}

# Versions the image must match, read from the checkout
locked_playwright="$(python3 -c '
import sys, tomllib
lock = tomllib.load(open(sys.argv[1], "rb"))
print(next(p["version"] for p in lock["package"] if p["name"] == "playwright"))
' "$root/uv.lock")"
project_version="$(python3 -c '
import sys, tomllib
print(tomllib.load(open(sys.argv[1], "rb"))["project"]["version"])
' "$root/pyproject.toml")"

# 1. Revision label
if [ -n "${EXPECTED_REVISION:-}" ]; then
  revision="$(docker inspect -f '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$image")"
  [ "$revision" = "$EXPECTED_REVISION" ] \
    || fail "revision label is '$revision', expected $EXPECTED_REVISION"
  echo "ok: revision label is $revision"
fi

# 2. Playwright version and a Firefox launch (the entrypoint is the server, so override it)
image_playwright="$(docker run --rm --entrypoint python "$image" -c \
  'import importlib.metadata as m; print(m.version("playwright"))')" \
  || fail "could not read the playwright version in the image"
[ "$image_playwright" = "$locked_playwright" ] \
  || fail "playwright in image is $image_playwright, uv.lock locks $locked_playwright"
echo "ok: playwright $image_playwright matches uv.lock"

docker run --rm --network none --entrypoint python "$image" -c '
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    page = browser.new_page()
    page.goto("about:blank")
    browser.close()
' || fail "headless Firefox did not launch"
echo "ok: headless Firefox launches"

# 3. --help
docker run --rm "$image" --help | grep -q "usage: mcp-mixsearch" \
  || fail "--help did not print the server's usage or exit 0"
echo "ok: --help prints the usage"

# 4 and 5. /health, fetched from inside the container (mode "inside", with no network) or from
# the host through a published port (mode "host")
fetch_health() {
  local mode="$1" name="$2" port="$3"
  local url
  if [ "$mode" = "inside" ]; then
    url="http://127.0.0.1:$port/health"
    docker exec "$name" python -c "
import urllib.request
print(urllib.request.urlopen('$url', timeout=2).read().decode())
" 2>/dev/null
  else
    local host_port
    host_port="$(docker port "$name" "$port/tcp" | head -n1 | sed 's/.*://')"
    [ -n "$host_port" ] || return 1
    python3 -c "
import urllib.request
print(urllib.request.urlopen('http://127.0.0.1:$host_port/health', timeout=2).read().decode())
" 2>/dev/null
  fi
}

check_health() {
  local mode="$1" name="$2" port="$3"
  shift 3
  local run_args=(-d --name "$name" -e MCP_AUTH_ENABLED=false)
  if [ "$mode" = "inside" ]; then
    run_args+=(--network none)
  else
    run_args+=(-p "127.0.0.1::$port")
  fi
  docker run "${run_args[@]}" "$image" "$@" >/dev/null || fail "could not start $name"
  containers+=("$name")
  local body="" deadline=$((SECONDS + timeout_s))
  while [ "$SECONDS" -lt "$deadline" ]; do
    if [ "$(docker inspect -f '{{.State.Running}}' "$name")" != "true" ]; then
      fail "$name exited before answering /health"
    fi
    if body="$(fetch_health "$mode" "$name" "$port")"; then
      break
    fi
    body=""
    sleep 1
  done
  [ -n "$body" ] || fail "$name did not answer /health on port $port within ${timeout_s}s"
  local reported
  reported="$(python3 -c 'import json, sys; print(json.loads(sys.argv[1])["version"])' "$body" \
    2>/dev/null)" || fail "/health returned a body without a version: $body"
  [ "$reported" = "$project_version" ] \
    || fail "/health reports version $reported, pyproject.toml has $project_version"
  echo "ok: $name answers /health on port $port ($mode), version $reported"
}

suffix="$$"
check_health inside "mcp-mixsearch-smoke-default-$suffix" 3000
check_health inside "mcp-mixsearch-smoke-port-$suffix" 3001 --port 3001
check_health host "mcp-mixsearch-smoke-published-$suffix" 3000

echo "smoke test passed: $image"
