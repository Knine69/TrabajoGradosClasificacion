#!/bin/sh

echo "Building and updating Langchain Docker Image..."

docker build -f user_langchain/Dockerfile -t jhuguet/langchain-executor:1.0.0 .
docker tag langchain-executor:1.0.0 jhuguet/langchain-executor:latest
docker push jhuguet/langchain-executor:1.0.0

echo "Building and updating Chroma Docker Image..."

docker build -f chroma/Dockerfile -t jhuguet/chroma-executor:1.0.0 .
docker tag chroma-executor:1.0.0 jhuguet/chroma-executor:latest
docker push jhuguet/chroma-executor:1.0.0
