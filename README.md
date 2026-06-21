# uwr-training

Monorepo for a web app: a Vite/React SPA front-end and a FastAPI back-end.

```
.
├── front-end/    # Vite + React + TypeScript + Tailwind SPA
├── api/          # FastAPI back-end (uv + ruff + mypy)
├── docker/       # Dockerfiles + compose for the dev stack and checker
├── Makefile      # entry points: make run / make check
└── render.yaml   # Render Blueprint (front-end static site)
```

Postgres is planned but not yet wired up.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (Desktop or Engine) running.

Everything runs in containers, so you don't need Node, Python, or any linter
installed on your host — only Docker.

## Run the dev stack

From the repo root:

```bash
make run                    # start everything: front-end + api (live reload)
make run service=front-end  # start only the front-end
make run service=api        # start only the api
make logs                   # follow live logs from all running containers
make logs service=api       # follow logs from a single service
make stop                   # stop and remove all containers
```

- Front-end: <http://localhost:5173>
- API: <http://localhost:8000> (docs at <http://localhost:8000/docs>)

`make run` starts the containers **in the background** and returns to your prompt;
use `make logs` to follow their output. Both services hot-reload when you edit
source on the host. The first run builds images and installs dependencies, so
expect it to take a minute; later runs are cached.

## Pre-commit checks

Code quality checks run through the [pre-commit](https://pre-commit.com) framework
**inside an ad-hoc Docker container**. The same container runs every check
(whitespace/EOF hygiene, YAML/JSON validation, ESLint + Prettier for the front-end,
and Ruff + mypy for the api), and only against files that changed.

```bash
make check
```

> [!NOTE]
> `pre-commit` only inspects **git-tracked** files. Stage new files with
> `git add` before running, or they'll be skipped.

This builds the checker image (first run only), then runs all hooks against every
tracked file. On the first run it also installs the front-end dependencies into a
named Docker volume. Subsequent runs reuse the cached image and hook environments.

### Optional: run on every commit automatically

`make check` runs the full suite on demand. If you also want hooks to fire on each
`git commit`, install pre-commit on your host and enable the git hook:

```bash
pipx install pre-commit   # or: brew install pre-commit
pre-commit install
```

This is independent of the Docker setup — it runs hooks on your host using the same
`.pre-commit-config.yaml`. Use whichever fits your workflow.

## Make targets

| Target                      | What it does                                               |
| --------------------------- | ---------------------------------------------------------- |
| `make run`                  | Start the full dev stack (front-end + api) in the background. |
| `make run service=<name>`   | Start a single service (`front-end`, `frontend`, or `api`). |
| `make logs`                 | Follow live logs from all running containers.              |
| `make logs service=<name>`  | Follow logs from a single service.                         |
| `make stop`                 | Stop and remove all running containers.                    |
| `make check`                | Run all pre-commit hooks in the checker container.         |
| `make pre-commit`           | Same as `make check`.                                      |
| `make build`                | Build all images.                                          |
| `make shell`                | Open a shell in the checker container for debugging.       |
| `make clean`                | Remove containers, images, and cache volumes.              |

## How it works

The `docker/` directory holds three pieces:

- **`Dockerfile`** + **`entrypoint.sh`** — the pre-commit **checker**
  (`python:3.12-slim` with git, Node 22, and the `pre-commit` framework). The
  entrypoint installs front-end deps on first run, then runs
  `pre-commit run --all-files`. `PRE_COMMIT_HOME` points at a cache volume so hook
  environments aren't rebuilt each run.
- **`frontend.Dockerfile`** — `node:22-slim` running the Vite dev server on port
  5173.
- **`api.Dockerfile`** — `python:3.12-slim` with [uv](https://docs.astral.sh/uv/),
  running `uvicorn --reload` on port 8000. Dependencies live in a venv at
  `/opt/venv`, outside the source mount.
- **`docker-compose.yml`** — defines the `frontend`, `api`, and `checker` services.
  Source is bind-mounted for live reload; named volumes keep Linux-native
  `node_modules` and the pre-commit cache separate from the host.

The `.pre-commit-config.yaml` hooks are scoped by path so front-end hooks only
touch `front-end/` and Python hooks (Ruff + mypy strict) only touch `api/`.

## Front-end

See [`front-end/`](front-end/) for the SPA. To work outside Docker, run these from
that directory:

```bash
npm install      # install dependencies
npm run dev      # start the dev server
npm run build    # type-check and build for production
npm run lint     # ESLint
npm run format   # Prettier
```

## API

See [`api/`](api/) for the FastAPI back-end, managed with
[uv](https://docs.astral.sh/uv/). To work outside Docker, run these from `api/`:

```bash
uv sync                              # install deps (incl. dev group)
uv run uvicorn app.main:app --reload # run locally
uv run ruff check .                  # lint
uv run ruff format .                 # format
uv run mypy .                        # type-check (strict)
```

## Configuration

The front-end talks to the API via an env var; the API restricts CORS via another.
Both have sensible localhost defaults, so **no setup is needed for local Docker dev**.

| Variable        | Service    | Default                 | Purpose                                   |
| --------------- | ---------- | ----------------------- | ----------------------------------------- |
| `VITE_API_URL`  | front-end  | `http://localhost:8000` | Base URL the SPA calls (baked at build).  |
| `CORS_ORIGINS`  | api        | `http://localhost:5173` | Comma-separated front-end origins to allow. |

For local overrides, copy [`front-end/.env.example`](front-end/.env.example) to
`front-end/.env`. On Render, both are set in [`render.yaml`](render.yaml).

## Deployment

Both services deploy to [Render](https://render.com) via the
[`render.yaml`](render.yaml) Blueprint, auto-deploying on push to the default branch:

- **`uwr-training-frontend`** — static site built from `front-end/`. Its `VITE_API_URL`
  points at the deployed API.
- **`uwr-training-api`** — Python web service from `api/`, built with `uv sync` and served
  by uvicorn on Render's `$PORT` (health check at `/health`). Its `CORS_ORIGINS`
  allows the front-end's origin.
