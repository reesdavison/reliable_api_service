#!/bin/sh


run_app() {
    # runs on port 8000 by default
    exec poetry run fastapi run app/main.py
}

echo "Running entrypoint"

if [ "$1" = "run_app" ]; then
    run_app
fi
