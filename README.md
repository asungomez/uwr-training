# uwr-training

Monorepo for a web app: a Vite/React SPA front-end and (planned) a FastAPI + Postgres back-end.

```
.
├── front-end/    # Vite + React + TypeScript + Tailwind SPA
├── back-end/     # FastAPI + Postgres (not yet scaffolded)
├── docker/       # Dockerized pre-commit checker
└── Makefile      # entry points for the checker
```

## Pre-commit checks

Code quality checks run through the [pre-commit](https://pre-commit.com) framework
**inside an ad-hoc Docker container**, so you don't need Python, Node, or any linter
installed on your host — only Docker. The same container runs every check
(whitespace/EOF hygiene, YAML/JSON validation, ESLint + Prettier for the front-end,
and Ruff for the back-end once it exists), and only against files that changed.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (Desktop or Engine) running.
- The repo must be a git repository with your files **tracked** — `pre-commit`
  only inspects git-tracked files. Stage new files with `git add` before running.

### Run the checks

From the repo root:

```bash
make check
```

This builds the checker image (first run only), then runs all hooks against every
tracked file. On the first run it also installs the front-end dependencies into a
named Docker volume — expect it to take a minute. Subsequent runs reuse the cached
image and hook environments.

### Make targets

| Target            | What it does                                              |
| ----------------- | --------------------------------------------------------- |
| `make check`      | Run all pre-commit hooks in the container (alias below).  |
| `make pre-commit` | Build if needed, run hooks on all files, then tear down.  |
| `make build`      | Build the checker image only.                             |
| `make shell`      | Open a shell in the checker container for debugging.      |
| `make clean`      | Remove the container, image, and cache volumes.           |

### How it works

- **`docker/Dockerfile`** — a `python:3.12-slim` image with git, Node 22, and the
  `pre-commit` framework. `PRE_COMMIT_HOME` points at a cache volume so hook
  environments aren't rebuilt each run.
- **`docker/docker-compose.yml`** — defines the `checker` service (container name
  `pre_commit`). It mounts the repo at `/repo`, plus two named volumes: one caching
  pre-commit environments and one holding Linux-native `front-end/node_modules`
  (kept separate from the host's macOS-built `node_modules`).
- **`docker/entrypoint.sh`** — installs front-end deps on first run, then runs
  `pre-commit run --all-files` (or any command you pass).
- **`.pre-commit-config.yaml`** — the hook definitions, scoped by path so front-end
  hooks only touch `front-end/` and back-end hooks only touch `back-end/`.

### Optional: run on every commit automatically

`make check` runs the full suite on demand. If you also want hooks to fire on each
`git commit`, install pre-commit on your host and enable the git hook:

```bash
pipx install pre-commit   # or: brew install pre-commit
pre-commit install
```

This is independent of the Docker setup — it runs hooks on your host using the same
`.pre-commit-config.yaml`. Use whichever fits your workflow.

## Front-end

See [`front-end/`](front-end/) for the SPA. Common scripts (run from that directory):

```bash
npm install      # install dependencies
npm run dev      # start the dev server
npm run build    # type-check and build for production
npm run lint     # ESLint
npm run format   # Prettier
```
