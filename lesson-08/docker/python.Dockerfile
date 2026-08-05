FROM python:3.12-slim

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash \
    && rm -rf /var/lib/apt/lists/*
