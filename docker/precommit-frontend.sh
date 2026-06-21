#!/usr/bin/env bash
# Runs a front-end lint/format tool (eslint|prettier) against the given files.
#
# The same pre-commit config runs in two contexts:
#   - Inside the checker container (PRECOMMIT_IN_CONTAINER=1, set on that service):
#     run the tool directly via npx using the container's node_modules. This is the
#     `make check` path; docker isn't available there, so we must not re-enter docker.
#   - From a host `git commit`: spin up an ad-hoc container off the checker image and
#     run the tool there. The host needs no node_modules of its own.
set -euo pipefail

tool="$1"
shift

# pre-commit passes repo-relative paths (front-end/...). The tools run with the
# front-end/ directory as the working dir, so strip that prefix.
files=()
for arg in "$@"; do
  files+=("${arg#front-end/}")
done

case "$tool" in
  eslint) cmd="npx eslint --fix --no-warn-ignored" ;;
  prettier) cmd="npx prettier --write --ignore-unknown" ;;
  *)
    echo "precommit-frontend: unknown tool '$tool'" >&2
    exit 2
    ;;
esac

# Already inside the checker container: run the tool directly.
if [ -n "${PRECOMMIT_IN_CONTAINER:-}" ]; then
  cd front-end
  exec $cmd "${files[@]}"
fi

# From the host: run in an ad-hoc container off the checker image. Its entrypoint
# installs front-end deps into the shared volume on first use, then execs this.
# Re-invoke this same script inside the container (PRECOMMIT_IN_CONTAINER short-circuit).
exec docker compose -f docker/docker-compose.yml run --rm -T \
  -e PRECOMMIT_IN_CONTAINER=1 checker \
  /repo/docker/precommit-frontend.sh "$tool" "${files[@]}"
