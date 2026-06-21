COMPOSE := docker compose -f docker/docker-compose.yml

.PHONY: check pre-commit run stop build shell clean

## check: run all pre-commit hooks inside an ad-hoc container
check: pre-commit

## pre-commit: build (if needed) and run pre-commit on all files
pre-commit:
	$(COMPOSE) build checker
	$(COMPOSE) run --rm checker
	$(COMPOSE) down --remove-orphans

## run: start the front-end dev server (hot-reload) at http://localhost:5173
run:
	$(COMPOSE) up --build frontend

## stop: stop and remove the front-end container
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
