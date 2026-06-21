COMPOSE := docker compose -f docker/docker-compose.yml

.PHONY: check pre-commit run logs stop build shell clean

## check: run all pre-commit hooks inside an ad-hoc container
check: pre-commit

## pre-commit: build (if needed) and run pre-commit on all files
pre-commit:
	$(COMPOSE) build checker
	$(COMPOSE) run --rm checker
	$(COMPOSE) down --remove-orphans

# `service` is optional. Unset → bring up the whole dev stack (frontend + api).
# Override to run just one, e.g. `make run service=front-end` or `make run service=api`.
# `front-end` is accepted as an alias for the `frontend` compose service.
service ?=
SERVICE := $(if $(service),$(patsubst front-end,frontend,$(service)),frontend api)

## run: start the dev stack (front-end + api) in the background with live reload.
## run service=<name>: start a single service (frontend|front-end|api).
run:
	$(COMPOSE) up --build --detach $(SERVICE)

## logs: follow live logs from the running containers.
## logs service=<name>: follow a single service (frontend|front-end|api).
logs:
	$(COMPOSE) logs --follow $(SERVICE)

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
