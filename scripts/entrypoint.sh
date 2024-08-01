#!/bin/sh


run_app() {
    # runs on port 8000 by default
    exec poetry run fastapi run app/main.py
}

migrate() {
    echo "Migrating"
    exec poetry run alembic "$@"
}

echo "Running entrypoint"

if [ "$1" = "run_app" ]; then
    run_app
elif [ "$1" = "migrate" ]; then
    shift
    migrate "$@"
fi
