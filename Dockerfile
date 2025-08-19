# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

WORKDIR /app

RUN pip install --no-cache-dir bagel

ENTRYPOINT [ "bagel" ]
CMD ["--help"]
