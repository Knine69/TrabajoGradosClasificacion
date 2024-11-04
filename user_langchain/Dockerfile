# Stage 1: Build Stage
FROM --platform=linux/amd64 python:3.9-slim as build-stage

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /langchain_app/bash_files

WORKDIR /langchain_app

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /langchain_app/wait-for-it.sh

RUN apt-get update && apt-get install -y bash gcc g++ make musl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/* && chmod +x /langchain_app/wait-for-it.sh

COPY user_langchain /langchain_app/user_langchain
COPY utils /langchain_app/utils
COPY documents /langchain_app/documents
COPY tools /langchain_app/tools
COPY langchain_ms_config.py /langchain_app/
COPY .env /langchain_app/

RUN ls -la && \
    mv user_langchain/initialize_langchain_services.sh bash_files/ && \
    python -m venv /langchain_app/.langchain && \
    /bin/bash -c ". /langchain_app/.langchain/bin/activate && pip install --no-cache-dir -r /langchain_app/user_langchain/requirements.txt"

# Stage 2: Runtime Stage
FROM --platform=linux/amd64 python:3.9-slim as runtime-stage

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=user_langchain/ \
    FLASK_ENV=development

RUN mkdir -p /langchain_app

WORKDIR /langchain_app

RUN apt-get update && apt-get install -y --no-install-recommends bash iputils-ping && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build-stage /langchain_app /langchain_app

EXPOSE 5001

# Set the command to start the application# Set the command to start the application using bash -c to execute wait-for-it
CMD ["/bin/bash", "-c", "./wait-for-it.sh redis:6379 -- ./wait-for-it.sh rabbitmq:5672 -- ./wait-for-it.sh chroma:8000 -- bash bash_files/initialize_langchain_services.sh"]
