# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/

ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/opt/poetry/'

RUN \
    # install system requirement
    apt update && \
    apt install -y iputils-ping curl && \
    # cleanup
    apt clean

# Copy the source code into the container.
# we're using a volume for that, but for initialization
COPY ./ /app/

WORKDIR /app/src/_example/django/

RUN curl -sSL https://install.python-poetry.org | python3 - ;\
    export PATH="/opt/poetry/bin:$PATH"

RUN /opt/poetry/bin/poetry install --no-cache

# for a bind mount on running repo
VOLUME /app

# Expose the port that the application listens on.
EXPOSE 8000

# set entrypoint
ENTRYPOINT ["/app/src/_example/django/docker-entrypoint.sh"]

# Run the application.
CMD /opt/poetry/bin/poetry run poe runserver
