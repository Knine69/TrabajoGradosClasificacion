FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=chroma/ \
    FLASK_ENV=development

RUN mkdir -p /chroma_app/chroma /chroma_app/bash_files

COPY . /chroma_app
WORKDIR /chroma_app

RUN apt-get update && apt-get install -y bash gcc g++ make musl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/* && ls -la && \
    bash -c 'shopt -s extglob && find . -maxdepth 1 -type f ! \( -name initialize_chroma_services.sh -o -name app_config.py \) -exec mv {} chroma/ \;' && \
    mv app category chroma/ && \
    mv initialize_chroma_services.sh bash_files/ && \
    touch .env && \
    python -m venv .chroma && \
    source .chroma/bin/activate && \
    pip install --no-cache-dir -r chroma/requirements.txt && \
    mkdir bash_files/chroma_server && \
    chmod -R 755 bash_files/chroma_server && \
    ls -la && ls -la bash_files/

CMD ["bash", "bash_files/initialize_chroma_services.sh", "8000"]
EXPOSE 5000