set shell := ["bash", "-euo", "pipefail", "-c"]
set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

default: setup

# Install the producer's dependencies.
setup:
    uv sync --locked

# Start Postgres (with pgvector) and RabbitMQ, and wait until both are healthy.
up:
    docker compose up -d --wait

# Stop everything and delete the volumes.
down:
    docker compose down -v

# Replay the registry feed onto the company-events queue.
publish:
    uv run python -m producer.publish

# Drop the database table
droptable:
    docker compose exec postgres psql -U postgres -d companies -c "DROP TABLE companies;"

# Check the count 
count:
    docker compose exec postgres psql -U postgres -d companies -c "SELECT COUNT(*) FROM companies;"
    
#Run consumer 
consumer:
    uv run python -m app.consumer

# Run the API server on port 8000.
interface:
    uv run uvicorn app.api:app --port 8000

# Run all tests (needs `just up` and the data loaded).
test:
    uv run pytest app/testing/test_api.py -v
    uv run pytest app/testing/test_normalization.py -v