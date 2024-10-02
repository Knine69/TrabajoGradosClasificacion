echo "Creating chroma persistance directory..."

mkdir chroma_server

echo "Building and updating Chroma Docker Image..."

docker build -f chroma/Dockerfile -t chroma-executor .
docker tag chroma-executor jhuguet/chroma-executor
docker push jhuguet/chroma-executor

echo "Building and updating Langchain Docker Image..."

docker build -f user_langchain/Dockerfile -t langchain-executor .
docker tag langchain-executor jhuguet/langchain-executor
docker push jhuguet/langchain-executor
