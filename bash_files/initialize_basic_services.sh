#!/bin/bash

OLLAMA_SCHED_SPREAD=true OLLAMA_NUM_PARALLEL=2 OLLAMA_GPU_OVERHEAD=1024M ollama serve & 

while ! nc -z localhost 11434; do
    echo "Waiting for llama service"
    sleep 2
done

echo "Llama is available"

wait

docker compose -f docker-compose.yml up
