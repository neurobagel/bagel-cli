# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

WORKDIR /app
COPY . /app/src
RUN pip install  --no-cache-dir /app/src[all]

ENTRYPOINT [ "bagelbids" ]