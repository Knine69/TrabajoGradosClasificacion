# Stage 1: Build Stage
FROM python:3.10-slim-bullseye AS build-stage

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create directories for the application
RUN mkdir -p /chroma_app/chroma /chroma_app/bash_files

# Set working directory
WORKDIR /chroma_app

# Install necessary build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    gcc \
    g++ \
    make \
    musl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . /chroma_app

# Set up virtual environment and install dependencies
RUN python -m venv /chroma_app/.chroma && \
    ls -la && \
    bash -c 'shopt -s extglob && find . -maxdepth 1 -type f ! \( -name initialize_chroma_services.sh -o -name app_config.py \) -exec mv {} chroma/ \;' && \
    bash -c ". /chroma_app/.chroma/bin/activate && pip install --no-cache-dir -r chroma/requirements.txt" && \
    mv app category chroma/ && \
    mv initialize_chroma_services.sh bash_files/ && \
    mkdir bash_files/chroma_server && \
    chmod -R 755 bash_files/chroma_server

# Stage 2: Final Stage (Runtime Image)
FROM python:3.10-slim-bullseye AS runtime-stage

# Set environment variables for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=chroma/ \
    FLASK_ENV=development

# Create the application directory
RUN mkdir -p /chroma_app

# Set working directory
WORKDIR /chroma_app

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy only the virtual environment and necessary files from build-stage
COPY --from=build-stage /chroma_app /chroma_app

# Expose the necessary port
EXPOSE 5000

# Set the command to start the application
CMD ["bash", "bash_files/initialize_chroma_services.sh", "8000"]
