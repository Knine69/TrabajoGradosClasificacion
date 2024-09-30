# Stage 1: Build Stage
FROM python:3.9-slim as build-stage

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create directories for the application
RUN mkdir -p /langchain_app/user_langchain /langchain_app/bash_files

# Set working directory
WORKDIR /langchain_app

# Install necessary build dependencies
RUN apt-get update && apt-get install -y bash gcc g++ make musl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy source code for the build
COPY . /langchain_app

# Move files around and set up virtual environment
RUN bash -c 'shopt -s extglob && find . -maxdepth 1 -type f ! \( -name initialize_langchain_services.sh -o -name app_config.py \) -exec mv {} user_langchain/ \;' && \
    mv app user_langchain/ && \
    mv initialize_langchain_services.sh bash_files/ && \
    touch .env && \
    python -m venv /langchain_app/.langchain && \
    /bin/bash -c ". /langchain_app/.langchain/bin/activate && pip install --no-cache-dir -r user_langchain/requirements.txt"

# Stage 2: Runtime Stage
FROM python:3.9-slim as runtime-stage

# Set environment variables for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=user_langchain/ \
    FLASK_ENV=development

# Create application directory
RUN mkdir -p /langchain_app

# Set working directory
WORKDIR /langchain_app

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends bash && \
    rm -rf /var/lib/apt/lists/*

# Copy only the necessary files and virtual environment from the build stage
COPY --from=build-stage /langchain_app /langchain_app

# Set the command to start the application
CMD ["bash", "bash_files/initialize_langchain_services.sh"]

# Expose the necessary port
EXPOSE 5001
