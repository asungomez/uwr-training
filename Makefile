COMPOSE := docker compose -f docker/docker-compose.yml

.PHONY: check pre-commit build shell clean

## check: run all pre-commit hooks inside an ad-hoc container
check: pre-commit

## pre-commit: build (if needed) and run pre-commit on all files
pre-commit:
	$(COMPOSE) build
	$(COMPOSE) run --rm checker
	$(COMPOSE) down --remove-orphans

## build: build the checker image
build:
	$(COMPOSE) build

## shell: open a shell in the checker container for debugging
shell:
	$(COMPOSE) run --rm checker bash

## clean: remove the container, image, and cache volumes
clean:
	$(COMPOSE) down --remove-orphans --volumes --rmi local
