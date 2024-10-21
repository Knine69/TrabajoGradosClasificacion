#!bin/bash

OLLAMA_SCHED_SPREAD=true OLLAMA_NUM_PARALLEL=2 OLLAMA_GPU_OVERHEAD=1024M ollama serve & \
docker compose -f docker-compose.yml up rabbitmq redis chroma
