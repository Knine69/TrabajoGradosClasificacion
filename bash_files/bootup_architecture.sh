#!/bin/bash

echo "Starting basic Docker services..." 
bash bash_files/initialize_basic_services.sh &

ports=(5672 6379)

# Function to check a single port
check_port() {
  local port=$1
  while ! nc -z localhost $port; do
    echo "Waiting for port $port to be ready..."
    sleep 3
  done
  echo "Port $port is ready!"
}

for port in "${ports[@]}"; do
  check_port $port &
done


echo "Starting Chroma Microservice"
bash chroma/initialize_chroma_services.sh
