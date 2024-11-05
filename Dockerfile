# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

WORKDIR /app
COPY . /app/src/

# To have a deterministic build, we
# 1. install the environment from our lockfile
RUN pip install -r /app/src/requirements.txt
# 2. install the CLI script without touching the dependencies again
RUN pip install --no-cache-dir --no-deps /app/src[all]

ENTRYPOINT [ "bagel" ]
CMD ["--help"]