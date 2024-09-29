FROM python:3.9-alpine
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=chroma/ \
    FLASK_ENV=development

RUN mkdir -p /chroma_app/chroma /chroma_app/bash_files

COPY . /chroma_app
WORKDIR /chroma_app

RUN apk update && apk add bash && \
    bash -c 'shopt -s extglob && mv !("initializa_chroma_services.sh") chroma/'  && \
    mv initializa_chroma_services.sh bash_files/ && \
    pip install -r ./chroma/requirements.txt

CMD ["bash", "bash_files/intialize_chroma_services.sh", "8000"]
EXPOSE 5000