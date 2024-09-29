FROM python:3.9-alpine
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=chroma/ \
    FLASK_ENV=development

WORKDIR /chroma_app
COPY ../chroma ../bash_files/initialize_chroma_services.sh ./

RUN <<EOF
apk update
pip install -r ./chroma/requirements.txt
EOF

CMD ["sh", "bash_files/intialize_chroma_services.sh", "8000"]
EXPOSE 5000