.PHONY: dev migrate seed quran-core api web test lint schema

export PYTHONUTF8=1

dev:            ## start infra (postgres, valkey, garage, mailpit) via docker compose
	docker compose --profile dev up -d

migrate:
	python apps/api/manage.py migrate

quran-core:     ## rebuild the Quran Core release from verified sources and load it (read-only tables)
	python -m packages.quran_core.build tmp/quran-uthmani.txt tmp/quran-data.xml
	python apps/api/manage.py load_quran_core

seed:           ## demo tenant with Arabic data and simulated Hifz history
	python apps/api/manage.py seed_demo --reset

api:
	python apps/api/manage.py runserver 0.0.0.0:8000

web:
	cd apps/admin-web && pnpm dev

schema:
	python apps/api/manage.py spectacular --file docs/api/openapi.yaml

test:
	python -m pytest -q

lint:
	ruff check . && ruff format --check . && lint-imports
