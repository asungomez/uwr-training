#!/usr/bin/env bash
# Ensures front-end deps exist inside the container (Linux-native, in a volume),
# then runs whatever command was passed (defaults to pre-commit on all files).
set -euo pipefail

if [ ! -x /repo/front-end/node_modules/.bin/eslint ]; then
  echo ">> Installing front-end dependencies inside container (first run)…"
  (cd /repo/front-end && npm ci)
fi

if [ "$#" -eq 0 ]; then
  exec pre-commit run --all-files
fi

exec "$@"
