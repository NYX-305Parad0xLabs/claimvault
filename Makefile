PY=python
PNPM=pnpm
API_DIR=apps/api
WEB_DIR=apps/web

install:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e $(API_DIR)
	$(PNPM) install

run-backend:
	$(PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	$(PNPM) --filter claimvault-web dev

lint-backend:
	cd $(API_DIR) && ruff check .

lint-web:
	cd $(WEB_DIR) && pnpm lint

docs:
	@echo "See docs/ for architectural context."

clean:
	@echo "Remove generated artifacts manually (e.g., node_modules, dist, __pycache__)."
