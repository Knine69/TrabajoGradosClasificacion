FROM python:3.9-alpine
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=user_langchain/ \
    FLASK_ENV=development

WORKDIR /langchain_app
COPY ../user_langchain ../bash_files/initialize_langchain_services.sh ./

RUN <<EOF
apk update
pip install -r ./user_langchain/requirements.txt
EOF

CMD ["sh", "bash_files/initialize_langchain_services.sh"]
EXPOSE 5001