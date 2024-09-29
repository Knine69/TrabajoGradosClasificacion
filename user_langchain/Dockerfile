FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=user_langchain/ \
    FLASK_ENV=development

RUN mkdir -p /langchain_app/user_langchain /langchain_app/bash_files

COPY . /langchain_app
WORKDIR /langchain_app

RUN apt-get update && apt-get install -y bash gcc g++ make musl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/* && ls -la && \
    bash -c 'shopt -s extglob && find . -maxdepth 1 -type f ! \( -name initialize_langchain_services.sh -o -name app_config.py \) -exec mv {} user_langchain/ \;'  && \
    mv app user_langchain/ && \
    mv initialize_langchain_services.sh bash_files/ && \
    touch .env && \
    python -m venv .langchain && \
    source .langchain/bin/activate && \
    pip install --no-cache-dir -r user_langchain/requirements.txt && \
    ls -la

CMD ["bash", "bash_files/initialize_langchain_services.sh"]
EXPOSE 5001