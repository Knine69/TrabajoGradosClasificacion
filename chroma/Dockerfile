FROM python:3.9-alpine
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=chroma/flask/ \
    FLASK_ENV=development

WORKDIR /app
COPY . ./

RUN <<EOF
apk update
pip install -r ./requirements.txt
EOF

CMD ["flask", "run", "--debug", "--host=0.0.0.0"]
EXPOSE 8000