PY=python
PNPM=pnpm
API_DIR=apps/api
WEB_DIR=apps/web

install:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e "$(API_DIR)[dev]"
	$(PNPM) install

api-dev:
	$(PY) -m uvicorn --factory apps.api.app.main:create_app --reload --host 0.0.0.0 --port 8000

api-test:
	cd $(API_DIR) && pytest

api-lint:
	cd $(API_DIR) && ruff check app tests

run-backend: api-dev

dev-web:
	$(PNPM) --filter claimvault-web dev

web-dev:
	cd $(WEB_DIR) && $(PNPM) dev

web-lint:
	cd $(WEB_DIR) && $(PNPM) lint

web-typecheck:
	cd $(WEB_DIR) && $(PNPM) typecheck

lint-backend: api-lint

lint-web:
	cd $(WEB_DIR) && pnpm lint

docs:
	@echo "See docs/ for architectural context."

clean:
	@echo "Remove generated artifacts manually (e.g., node_modules, dist, __pycache__)."
