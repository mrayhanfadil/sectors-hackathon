# Docker workflow for the report app. `make help` lists everything.
#
# The point of the split: `build` is the only slow command, and it stays fast because the images install
# dependencies in a layer that a source change does not invalidate (see docs/docker.md).

SHELL := /bin/bash
COMPOSE := docker compose
TICKER ?= AMMN

.PHONY: help build build-slim rebuild up down restart logs ps sh test api-health pdf pdf-open shell-web clean nuke

help: ## list targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

build: ## build both images (cached; source changes do not reinstall dependencies)
	$(COMPOSE) build

build-slim: ## build the API image without the Google ADK stack (report + PDF only)
	$(COMPOSE) build --build-arg WITH_ADK=false api

rebuild: ## force a clean rebuild of the API image, no layer cache
	$(COMPOSE) build --no-cache api

up: ## start the stack in the background
	$(COMPOSE) up -d

down: ## stop the stack (named volumes and bind mounts are kept)
	$(COMPOSE) down

restart: ## restart the API container only
	$(COMPOSE) restart api

logs: ## follow logs from both services
	$(COMPOSE) logs -f --tail=120

ps: ## show container status and health
	$(COMPOSE) ps

sh: ## shell inside the API container
	$(COMPOSE) exec api bash

shell-web: ## shell inside the web container
	$(COMPOSE) exec web sh

test: ## run the test suite inside the API container
	$(COMPOSE) exec api python -m pytest tests/ -q -p no:randomly

api-health: ## ask the API for /api/health through nginx (same origin as the browser uses)
	@curl -s -A "Mozilla/5.0" http://127.0.0.1:8080/api/health | head -c 400; echo

pdf: ## render the deck inside the container and copy it out to output/
	$(COMPOSE) exec -T api python -c "import asyncio, sys; sys.path.insert(0, '.'); \
	from server.routers.pdf import render_pdf_bytes_for_ticker as r; \
	pdf, engine, tpl, _ = asyncio.run(r('$(TICKER)')); \
	open('/app/output/$(TICKER)_docker.pdf', 'wb').write(pdf); \
	print('rendered', len(pdf), 'bytes via', engine, '->', tpl)"

clean: ## remove the images built by this compose file
	-$(COMPOSE) down --rmi local

nuke: ## stop everything and drop the harvest cache volume mounts (host data/ and output/ are untouched)
	-$(COMPOSE) down -v
