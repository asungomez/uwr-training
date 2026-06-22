COMPOSE := docker compose -f docker/docker-compose.yml

.PHONY: check pre-commit run logs admin gen-api test test-setup stop build shell clean

## test: run the e2e suite. uv syncs the locked env (fetching Python 3.12 if
## needed) on first run; containers use random ports so a live dev stack is safe.
test: test-setup
	cd tests && uv run pytest

# Sync the locked test env + ensure the Playwright browser is installed.
test-setup:
	cd tests && uv sync && uv run playwright install chromium

## check: run all pre-commit hooks inside an ad-hoc container
check: pre-commit

## pre-commit: build (if needed) and run pre-commit on all files
## `run --rm` removes the checker container on exit; the dev stack is left running.
pre-commit:
	$(COMPOSE) build checker
	$(COMPOSE) run --rm checker

# `service` is optional. Unset → bring up the whole dev stack (frontend + api + db).
# Override to run just one, e.g. `make run service=front-end` or `make run service=db`.
# `front-end` is accepted as an alias for the `frontend` compose service.
service ?=
SERVICE := $(if $(service),$(patsubst front-end,frontend,$(service)),frontend api db)

## run: start the dev stack (front-end + api + db) in the background with live reload.
## run service=<name>: start a single service (frontend|front-end|api|db).
run:
	$(COMPOSE) up --build --detach $(SERVICE)

## logs: follow live logs from the running containers.
## logs service=<name>: follow a single service (frontend|front-end|api|db).
logs:
	$(COMPOSE) logs --follow $(SERVICE)

# `make admin command='create-admin a@b.c'` runs the admin CLI in a one-off
# container against the local db. Pass db-connection-string='<url>' to target a
# remote DB (e.g. Render's external connection string). Quote args with spaces.
admin:
	@test -n "$(command)" || { echo "usage: make admin command='create-admin a@b.c' [db-connection-string='<url>']"; exit 1; }
	ADMIN_DATABASE_URL='$(db-connection-string)' $(COMPOSE) run --rm admin uv run python -m app.cli $(command)

## gen-api: regenerate front-end TypeScript types from the API's OpenAPI spec.
## Requires the api service running (`make run`); reads the spec over the compose network.
gen-api:
	$(COMPOSE) exec -e API_OPENAPI_URL=http://api:8000/openapi.json frontend npm run gen:api

## stop: stop and remove all running containers
stop:
	$(COMPOSE) down --remove-orphans

## build: build all images
build:
	$(COMPOSE) build

## shell: open a shell in the checker container for debugging
shell:
	$(COMPOSE) run --rm checker bash

## clean: remove containers, images, and cache volumes
clean:
	$(COMPOSE) down --remove-orphans --volumes --rmi local
