.PHONY: install lint test ingest ingest-sample eval backend frontend dev api

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest

ingest:
	python scripts/ingest_sources.py $(if $(source),--source $(source),) $(if $(output),--output $(output),)

ingest-sample:
	python scripts/ingest_sources.py --sample-only $(if $(output),--output $(output),)

eval:
	python scripts/run_eval.py $(if $(eval_path),--eval-path $(eval_path),)

backend:
	uvicorn devdocs_rag.api:app --reload

frontend:
	cd frontend && npm run dev

dev:
	$(MAKE) backend & cd frontend && npm run dev

api:
	uvicorn devdocs_rag.api:app --reload
