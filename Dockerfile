FROM python:3.11

WORKDIR /workspace

# Install deps in stage 1
# could be separated into separate build steps
# as deps should change less frequently
COPY pyproject.toml poetry.lock ./
RUN pip install poetry
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN poetry config virtualenvs.path "/opt/venv"
# RUN poetry config virtualenvs.create false
RUN poetry install --no-directory --no-root --only main 

COPY scripts/entrypoint.sh entrypoint.sh
COPY app app
# RUN poetry install --root-only

ENTRYPOINT ["/bin/sh", "entrypoint.sh"]