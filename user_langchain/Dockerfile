FROM python:3.9-alpine
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=user_langchain/ \
    FLASK_ENV=development


RUN mkdir -p /langchain_app/user_langchain /langchain_app/bash_files

COPY . /langchain_app
WORKDIR /langchain_app

RUN apk update && apk add bash && \
    bash -c 'shopt -s extglob && mv !("initializa_langchain_services.sh") user_langchain/'  && \
    mv initializa_langchain_services.sh bash_files/ && \
    pip install -r ./user_langchain/requirements.txt


CMD ["bash", "bash_files/initialize_langchain_services.sh"]
EXPOSE 5001