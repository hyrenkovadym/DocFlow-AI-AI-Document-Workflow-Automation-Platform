# DocFlow API

## Local run

```bash
pip install -e .[dev]
uvicorn app.main:app --reload --port 8000
```

## Worker

```bash
celery -A app.workers.celery_app.celery_app worker -l info
```

## Migrations

```bash
alembic upgrade head
```

## Seed

```bash
python -m app.scripts.seed
```
