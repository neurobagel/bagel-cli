# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

WORKDIR /app
COPY ./entrypoint.sh /app/src/entrypoint.sh

RUN chmod +x /app/src/entrypoint.sh

RUN pip install --no-cache-dir bagel

ENTRYPOINT [ "/app/src/entrypoint.sh" ]
CMD ["--help"]