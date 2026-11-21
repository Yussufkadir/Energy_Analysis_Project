.PHONY: up down logs backfill models export test psql

START ?= 2024-01-01
END   ?= 2025-01-01

up:            ## start Airflow + Postgres (UI on http://localhost:8080)
	docker compose up -d --build

down:          ## stop everything (data volumes are kept)
	docker compose down

logs:
	docker compose logs -f airflow

backfill:      ## one-off historical load: make backfill START=2024-01-01 END=2025-01-01
	docker compose exec airflow python -m eia_pipeline run --start $(START) --end $(END)

models:        ## rebuild staging views and marts
	docker compose exec airflow python -m eia_pipeline models

export:        ## write marts to exports/*.csv
	docker compose exec airflow python -m eia_pipeline export

psql:          ## open a SQL shell on the warehouse
	docker compose exec warehouse psql -U energy -d energy

test:
	python -m pytest -q
