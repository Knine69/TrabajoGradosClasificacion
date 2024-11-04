# Stage 1: Build Stage
FROM --platform=linux/amd64 python:3.10-slim AS build-stage

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /chroma_app/bash_files

WORKDIR /chroma_app

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /chroma_app/wait-for-it.sh

RUN apt-get update && apt-get install -y --no-install-recommends bash gcc g++ make musl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/* && chmod +x /chroma_app/wait-for-it.sh

COPY chroma /chroma_app/chroma
COPY documents /chroma_app/documents
COPY utils /chroma_app/utils
COPY chroma_ms_config.py /chroma_app/

RUN touch .env && ls -la && \
    mv chroma/initialize_chroma_services.sh bash_files/ && \
    python -m venv /chroma_app/.chroma && \
    bash -c ". /chroma_app/.chroma/bin/activate && pip install --no-cache-dir -r chroma/requirements.txt" && \
    pip install sentence-transformers==2.2.2 --no-deps

# Stage 2: Final Stage (Runtime Image)
FROM python:3.10-slim AS runtime-stage

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=chroma/ \
    FLASK_ENV=development

RUN mkdir -p /chroma_app

WORKDIR /chroma_app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build-stage /chroma_app /chroma_app

EXPOSE 5000

CMD ["/bin/bash", "-c", "./wait-for-it.sh redis:6379 -- ./wait-for-it.sh rabbitmq:5672 -- ./wait-for-it.sh chroma:8000 -- bash bash_files/initialize_chroma_services.sh"]
