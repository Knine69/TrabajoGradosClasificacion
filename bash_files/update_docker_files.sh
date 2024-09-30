echo "Building and updating Chroma Docker Image..."

cd chroma/ || exit
docker build -t chroma-executor .
docker tag chroma-executor jhuguet/chroma-executor
docker push jhuguet/chroma-executor
cd ..

echo "Building and updating Langchain Docker Image..."

cd user_langchain/ || exit
docker build -t langchain-executor .
docker tag langchain-executor jhuguet/langchain-executor
docker push jhuguet/langchain-executor
