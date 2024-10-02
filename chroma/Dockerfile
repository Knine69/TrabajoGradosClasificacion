# Stage 1: Build Stage
FROM python:3.10-slim-bullseye AS build-stage

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create directories for the application
RUN mkdir -p /chroma_app/bash_files

# Set working directory
WORKDIR /chroma_app

# Install necessary build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends bash gcc g++ make musl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy source code
COPY chroma /chroma_app/chroma
COPY app_config.py utils documents /chroma_app/


# Set up virtual environment and install dependencies
RUN touch .env && ls -la && \
    mv chroma/initialize_chroma_services.sh bash_files/ && \
    python -m venv /chroma_app/.chroma && \
    bash -c ". /chroma_app/.chroma/bin/activate && pip install --no-cache-dir -r chroma/requirements.txt"


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
CMD ["bash", "bash_files/initialize_chroma_services.sh"]
