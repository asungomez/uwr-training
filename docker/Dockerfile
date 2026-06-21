# Ad-hoc image for running monorepo pre-commit checks.
# Bundles git + Python (for the pre-commit framework) + Node (for eslint/prettier).
FROM python:3.12-slim

# Node 22 (needed by ESLint 10 / the front-end toolchain) + git.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pre-commit

# The repo is bind-mounted at /repo and owned by the host user, so tell git to trust it.
RUN git config --system --add safe.directory /repo

# Cache pre-commit hook environments here (mounted as a named volume).
ENV PRE_COMMIT_HOME=/cache/pre-commit

WORKDIR /repo
