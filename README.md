# uwr-training

Monorepo for a web app: a Vite/React SPA front-end, a FastAPI back-end, and a
Postgres database.

```
.
├── front-end/    # Vite + React + TypeScript + Tailwind SPA
├── api/          # FastAPI back-end (uv + ruff + mypy + SQLAlchemy/Alembic)
├── tests/        # Playwright + testcontainers e2e suite (Python)
├── docker/       # Dockerfiles + compose for the dev stack and checker
├── Makefile      # entry points: make run / make check / make test
└── render.yaml   # Render Blueprint (front-end, api, database)
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (Desktop or Engine) running.

Everything runs in containers, so you don't need Node, Python, or any linter
installed on your host — only Docker.

## Run the dev stack

From the repo root:

```bash
make run                    # start everything: front-end + api + db (live reload)
make run service=front-end  # start only the front-end
make run service=api        # start only the api (also starts db, its dependency)
make run service=db         # start only the database
make logs                   # follow live logs from all running containers
make logs service=api       # follow logs from a single service
make stop                   # stop and remove all containers
```

- Front-end: <http://localhost:5173>
- API: <http://localhost:8000> (docs at <http://localhost:8000/docs>)
- Database: Postgres on `localhost:5432` (user/password/db all `uwr`)

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
The checker container is removed when it finishes, and any running dev stack
(`make run`) is left untouched.

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
| `make run`                  | Start the full dev stack (front-end + api + db) in the background. |
| `make run service=<name>`   | Start a single service (`front-end`, `frontend`, `api`, or `db`). |
| `make logs`                 | Follow live logs from all running containers.              |
| `make logs service=<name>`  | Follow logs from a single service.                         |
| `make admin command='...'`  | Run an admin CLI command (e.g. `create-admin`) in a one-off container. |
| `make gen-api`              | Regenerate front-end TS types from the API's OpenAPI spec. |
| `make test`                 | Run the e2e suite (auto-creates the test venv on first run). |
| `make stop`                 | Stop and remove all running containers.                    |
| `make check`                | Run all pre-commit hooks in the checker container.         |
| `make pre-commit`           | Same as `make check`.                                      |
| `make build`                | Build all images.                                          |
| `make shell`                | Open a shell in the checker container for debugging.       |
| `make clean`                | Remove containers, images, and cache volumes.              |

## How it works

The `docker/` directory is laid out as:

```
docker/
  docker-compose.yml
  dockerfiles/   checker · frontend · api  (one .Dockerfile per service)
  entrypoints/   checker.sh
```

- **`dockerfiles/checker.Dockerfile`** + **`entrypoints/checker.sh`** — the
  pre-commit **checker** (`python:3.12-slim` with git, Node 22, and the
  `pre-commit` framework). The entrypoint installs front-end deps on first run,
  then runs `pre-commit run --all-files`. `PRE_COMMIT_HOME` points at a cache
  volume so hook environments aren't rebuilt each run.
- **`dockerfiles/frontend.Dockerfile`** — `node:22-slim` running the Vite dev
  server on port 5173.
- **`dockerfiles/api.Dockerfile`** — `python:3.12-slim` with
  [uv](https://docs.astral.sh/uv/), running `uvicorn --reload` on port 8000.
  Dependencies live in a venv at `/opt/venv`, outside the source mount.
- **`docker-compose.yml`** — defines the `frontend`, `api`, `db`, `minio` (+ a
  one-off `minio-setup` that creates the public-read media bucket), `checker`, and
  one-off `admin` services. Source is bind-mounted for live reload; named volumes
  keep Linux-native `node_modules` and the pre-commit cache separate from the host.
  [MinIO](https://min.io/) is an S3-compatible store for exercise media (thumbnails
  + videos): the API mints presigned upload URLs so the browser uploads straight to
  it (console at `localhost:9001`, S3 API at `localhost:9000`). In production this is
  a real S3 bucket, configured via the `S3_*` env vars.

The `.pre-commit-config.yaml` hooks are scoped by path so Python hooks (Ruff + mypy
strict) only touch `api/`. The front-end ESLint/Prettier hooks run via
[`front-end/precommit.sh`](front-end/precommit.sh), which executes them in the
checker image — so neither the host nor a running dev stack needs `node_modules`.

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

### API client (typed, SWR)

The front-end talks to the API through a **typed client generated from the API's
OpenAPI spec** — no hand-written types or fetchers:

- [`openapi-typescript`](https://openapi-ts.dev/) generates `src/api/schema.d.ts`
  from `/openapi.json` (committed; types only, no runtime code).
- [`openapi-fetch`](https://openapi-ts.dev/openapi-fetch/) + [`swr-openapi`](https://github.com/htunnicliff/swr-openapi)
  provide the typed client and SWR hooks in `src/api/client.ts`.

Regenerate the types whenever the API contract changes (requires the api running):

```bash
make gen-api
```

Auth state lives in a global context ([`src/auth/`](front-end/src/auth/)):
`AuthProvider` uses SWR on `/auth/me` as the source of truth, and exposes
`useAuth()` with `user`, `isLoading`, `login`, and `logout`. All requests send the
session cookie (`credentials: include`).

Forms use [React Hook Form](https://react-hook-form.com/) with
[Zod](https://zod.dev/) schemas (via `@hookform/resolvers`) for validation.
Icons come from [lucide-react](https://lucide.dev/).

Routing uses [React Router](https://reactrouter.com/). Unauthenticated users see the
login screen; authenticated users get the app shell
([`src/components/features/layout/`](front-end/src/components/features/layout/)): a top
navbar (app name centered, user menu with logout on the right), a left sidebar
(collapsible via a hamburger on mobile), and the routed page content. The sidebar's
"Administración" section (e.g. Usuarios) and its routes are admin-only — members are
redirected away.

**Source layout**: `src/pages/` contains only pages, in URL-shaped directories
(`pages/users/UsersPage.tsx`, `pages/users/[id]/UserDetailPage.tsx`). Shared UI lives
in `src/components/` split by atomic design — `atoms/`, `molecules/`, and
`features/<area>/`. Cross-module imports use the `@/` alias (→ `src/`), e.g.
`import Modal from '@/components/atoms/Modal'`.

## API

See [`api/`](api/) for the FastAPI back-end, managed with
[uv](https://docs.astral.sh/uv/). To work outside Docker, run these from `api/`:

```bash
uv sync                              # install deps (incl. dev group)
uv run uvicorn app.main:app --reload # run locally
uv run ruff check .                  # lint
uv run ruff format .                 # format
uv run mypy app                      # type-check (strict)
```

### Database & migrations

The API uses **SQLAlchemy 2.0 (async, asyncpg)** with **Alembic** for migrations.
Models live in [`api/app/models.py`](api/app/models.py); migrations in
`api/alembic/versions/`. With the stack running, manage schema from inside the
api container:

```bash
docker compose -f docker/docker-compose.yml exec api \
  uv run alembic revision --autogenerate -m "describe change"   # create a migration
docker compose -f docker/docker-compose.yml exec api \
  uv run alembic upgrade head                                   # apply migrations
```

`GET /db-health` runs `SELECT 1` to confirm connectivity.

### Authentication & admin users

Auth is **invitation-only**: there's no public sign-up. Admins invite other users;
the `users` and `invitations` tables back this. Passwords are hashed with bcrypt.

Because there's no first admin to send the first invite (and Render's free tier has
no shell), bootstrap an admin with the `make admin` CLI, which runs in a one-off
container:

```bash
# Against the local dev database (prompts for a password):
make admin command='create-admin you@example.com'

# Against a remote database (e.g. Render's *external* connection string):
make admin command='create-admin you@example.com' \
  db-connection-string='postgresql://user:pass@host/db'
```

`create-admin` lowercases the email, hashes the password, and creates the admin —
or, if the user already exists, promotes them to an active admin (idempotent). Pass
`--password` inside `command` to skip the prompt (avoid in shared shells).

#### Login

`POST /auth/login` takes `{email, password}` and, on success, sets an **HTTP-only
session cookie** holding a signed JWT (no server-side session store). Related routes:

| Route               | Purpose                                              |
| ------------------- | ---------------------------------------------------- |
| `POST /auth/login`  | Validate credentials, set the session cookie.        |
| `GET /auth/me`      | Return the current user (401 if no/invalid cookie).  |
| `POST /auth/logout` | Clear the session cookie.                            |

The cookie is signed with `SECRET_KEY` and marked `Secure` unless `COOKIE_SECURE=false`
(set that for local plain-HTTP testing in a browser).

#### Invitations

After the first admin exists, further users join by invitation (no public sign-up).
The flow is API-only for now — there's **no email integration**; the admin shares the
returned link manually (copy-paste).

| Route                                  | Auth        | Purpose                                                                 |
| -------------------------------------- | ----------- | ----------------------------------------------------------------------- |
| `POST /auth/invitations`               | Admin       | Create a member invitation; returns the raw `token` **once** (only its hash is stored). |
| `GET /auth/invitations/{token}`        | Public      | Validate a token and return the invitee email/role for the accept screen. |
| `POST /auth/invitations/{token}/accept`| Public      | Set a password → create the member user and consume the invitation.     |

Invitations are member-only, expire after 7 days, and can be accepted once. Validation
errors: `404` unknown/used token, `410` expired, `409` email already a user, `403`
non-admin create.

## Tests

End-to-end tests live in [`tests/`](tests/) — **Playwright** driving a real browser
against the full stack, which [testcontainers](https://testcontainers.com/) spins up
just for the run. Tests are grouped by area (e.g. [`tests/auth/`](tests/auth/)) and
follow a **given / when / then** structure: arrange the system (seed the DB,
authenticate…), interact with the UI, then assert on the UI.

```bash
make test
```

`tests/` is a [uv](https://docs.astral.sh/uv/) project (`pyproject.toml` + `uv.lock`,
pinned to Python 3.12 to match the API). The first `make test` runs `uv sync` —
fetching Python 3.12 if needed, installing the locked deps and the `api` package
editable (so tests reuse its SQLAlchemy models) — plus the Playwright browser, then
runs `pytest`. Subsequent runs reuse the synced env.

How it works ([`tests/conftest.py`](tests/conftest.py)):

- A session fixture starts `db`, `api`, and `frontend` containers on a **private
  network** (built from the same `docker/dockerfiles/*`), then runs
  `alembic upgrade head` in the api container.
- Containers bind to **random host ports**, so `make test` runs fine alongside a
  live `make run` dev stack — nothing clashes on 5173/8000/5432.
- An autouse fixture **truncates every table** before each test, so tests start
  from an empty database.

### Test data factories

Seeding lives under [`tests/seeding/`](tests/seeding/), one package per model (e.g.
`seeding/user/` with `factory.py` + `fixtures.py`). Factories build model instances
with mandatory fields auto-filled by [Faker](https://faker.readthedocs.io/); pass
overrides only for what the test cares about. The user fixtures (registered via
`pytest_plugins`):

- **`generate_user(**overrides)`** — returns an **in-memory** `User` (not persisted).
- **`create_user(**overrides)`** — persists one and returns the detached instance.

```python
def test_admin_thing(create_user):
    admin = create_user(role="admin")   # email/password/… auto-filled
    # log in with factories.DEFAULT_PASSWORD
```

## Configuration

The front-end calls the API at the **same-origin `/api` path**, which is proxied to
the back-end — by the Vite dev server locally, and by a Render rewrite in production.
This means the front-end needs no API URL and there's no cross-origin request (so no
CORS to configure). Every variable has a sensible default, so **no setup is needed
for local Docker dev**.

| Variable            | Service    | Default                                           | Purpose                                                                 |
| ------------------- | ---------- | ------------------------------------------------- | ----------------------------------------------------------------------- |
| `API_PROXY_TARGET`  | front-end  | `http://localhost:8000` (compose: `http://api:8000`) | Dev-only: where the Vite dev server forwards `/api`.                 |
| `VITE_API_URL`      | front-end  | `/api`                                            | Optional override to call an absolute API URL instead of the proxy.     |
| `CORS_ORIGINS`      | api        | `http://localhost:5173`                           | Comma-separated origins allowed by CORS (only matters for direct, cross-origin calls; unused in the proxy setup). |
| `DATABASE_URL`      | api        | `postgresql+asyncpg://uwr:uwr@localhost:5432/uwr` | Postgres connection string. A `postgresql://` scheme is auto-rewritten for asyncpg. |
| `SECRET_KEY`        | api        | `dev-secret-change-me`                            | Signs session-cookie JWTs. On Render, generated and kept stable. **Set a real value in any non-local env.** |
| `COOKIE_SECURE`     | api        | `true`                                            | When `true`, the session cookie is `Secure` (HTTPS only). Set `false` for local plain-HTTP browser testing. |

The api's settings are centralized and typed in
[`api/app/settings.py`](api/app/settings.py) (`pydantic-settings`); each variable
above maps to a field there with its type and default.

For local overrides, copy [`front-end/.env.example`](front-end/.env.example) to
`front-end/.env`. On Render, these are set in [`render.yaml`](render.yaml).

## Deployment

Everything deploys to [Render](https://render.com) via the
[`render.yaml`](render.yaml) Blueprint, auto-deploying on push to the default branch:

- **`uwr-training-frontend`** — static site built from `front-end/`. A rewrite rule
  proxies `/api/*` to the API service, so the SPA stays same-origin and needs no API
  URL of its own.
- **`uwr-training-api`** — Python web service from `api/`, built with `uv sync` and served
  by uvicorn on Render's `$PORT` (health check at `/health`). `DATABASE_URL` is injected
  from the database. The start command runs `alembic upgrade head` before launching, so
  migrations apply on each deploy.
- **`uwr-training-db`** — managed Postgres (free plan). `DATABASE_URL` is wired into
  the api automatically via `fromDatabase`.

> [!NOTE]
> The front-end's `/api/*` rewrite destination in `render.yaml` is the one place the
> API's public URL is referenced. Render can't inject a service's public URL into a
> static site, so if you rename the API service or its URL changes, update that
> destination.

> [!NOTE]
> On Render's free tier the web service spins down when idle (slow first request),
> and free Postgres databases expire after a set period — fine for dev/demo, not
> production.
