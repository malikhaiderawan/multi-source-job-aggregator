.PHONY: dev dev-backend dev-frontend test

dev:
	@$(MAKE) -j 2 dev-backend dev-frontend

dev-backend:
	.venv/bin/uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	.venv/bin/pytest tests/ -v