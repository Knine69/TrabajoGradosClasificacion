#!/bin/sh

echo "Building and updating Langchain Docker Image..."

docker build -f user_langchain/Dockerfile -t langchain-executor .
docker tag langchain-executor jhuguet/langchain-executor
docker push jhuguet/langchain-executor
