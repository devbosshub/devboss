#!/bin/sh
set -eu

mkdir -p /root/.codex

if [ -n "${DEVBOSS_CODEX_AUTH_JSON:-}" ]; then
  printf '%s' "$DEVBOSS_CODEX_AUTH_JSON" > /root/.codex/auth.json
  chmod 600 /root/.codex/auth.json
fi

exec python -m runtime.main
