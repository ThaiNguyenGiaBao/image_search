WORKER_CONCURRENCY ?= 4
LOGLEVEL ?= INFO
FLOWER_PORT ?= 5555

# Start Celery worker
worker:
	source .venv/bin/activate && \
	cd src && \
	PRELOAD_MODEL=1  celery -A celery_app worker --loglevel=$(LOGLEVEL) --concurrency=$(WORKER_CONCURRENCY) 

# Start Flower monitoring UI
flower:
	source .venv/bin/activate && \
	cd src && \
	celery -A celery_app flower --port=$(FLOWER_PORT) 

producer:
	source .venv/bin/activate && \
	cd src && \
	START_BATCH=${START_BATCH} python producer.py

encoder_api:
	source .venv/bin/activate && \
	cd src && \
	uvicorn embedding.api:app

qdrant_performance:
	source .venv/bin/activate && \
	cd src && \
	PYTHONPATH=. python performence/performence_qdrant.py

model_performance:
	source .venv/bin/activate && \
	cd src && \
	PYTHONPATH=. python performence/performence_model.py
