## Setup Process:


### Python version required:

This project as of today, requires the use of python 3.9.13 =<


#### Dependencies installation:

In order to solve possible issues that may arise, run the following dependencies' installation:

```
    pip torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install --upgrade pymupdf
```

TODO: Pip install the requirements for the chroma microservices (Langchain is not required, as is container)

For a whole dependency installation run:

```commandline
    pip install -r requirements.txt
```

#### Create .env configuration file

Using your preferred code editor, create a `.env` file that will load environment variables to our applications:

```text
# .env file
RABBIT_BROKER_URL=pyamqp://guest@localhost//
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CHROMA_QUEUE=chroma_queue
LANGCHAIN_QUEUE=langchain_queue
```

#### Ollama Installation

In order to install Ollama, as a root user the process is simple, simply run:

```commandline
    # Download and install ollama 
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Check if Ollama was installed in terminal
    ollama
    
    # Serve Ollama in a separate terminal
    OLLAMA_SCHED_SPREAD=true OLLAMA_NUM_PARALLEL=2 OLLAMA_GPU_OVERHEAD=1024M ollama serve
    
    # Check ollama version
    ollama -v
```

If, on the other hand, you wish to install ollama as a non-root user, then follow the next instructions:

```commandline
    # Run sh in shell files in repo
        cd bash_files/
        sh install.sh
    
    # Verify ollama was installed locally after installation finishes
        ls ~/.local/bin/ollama
    
    # Add local variable path into path variable to enable running ollama
        nano ~/.bashrc
        # Add at end of file
            export PATH=$HOME/.local/bin:$PATH
        # Reload your configuration in .bashrc 
            source ~/.bashrc 
        
    # Verify that path was correctly exported
        echo $PATH
    
    # Check ollama is working
        ollama
        
    # Check ollama version
         ollama --version
         
         # Run in separate terminal if ollama version does not work and try again
            OLLAMA_SCHED_SPREAD=true OLLAMA_NUM_PARALLEL=2 OLLAMA_GPU_OVERHEAD=1024M ollama serve
         
    
```

#### Install LLM Ollama models

In order to get fine-tunned models which are created for chat/dialogue use cases:
```commandline
    # 40 GB model
    ollama run llama3:70b-instruct
    
    # 49 GB model
    ollama run llama3:70b-instruct-q5_K_S
    
    # 58 GB model
    ollama run llama3:70b-instruct-q6_K
    
    # 75 GB model
    ollama run llama3:70b-instruct-q8_0
```

To install a pre-trained base model then run: 

```commandline
    # 40 GB model
    ollama run llama3:70b-text
    
    # 49 GB model
    ollama run llama3:70b-text-q5_0
    
    # 58 GB model
    ollama run llama3:70b-text-q6_K
    
    # 75 GB model
    ollama run llama3:70b-text-q8_0
```

To check for more available models, look into: 

https://ollama.com/library

### Tools and services installations

#### Install docker


It is necessary to install docker in order to host the containers that will expose the services and microservices required for the correct execution of the application. That being the case, to be able to use docker, follow the next steps to install the needed tools:

```commandline

    # Ubuntu
    sudo apt-get update
    # <arch> is to be replaced with your choosen architecture. Ignore resulting error message.
    sudo apt-get install ./docker-desktop-<arch>.deb

    # Start the docker service
    systemctl --user start docker-desktop

    # Start the docker service
    systemctl --user stop docker-desktop

    # Check docker version
    docker --version

```

The set of commands shown before should have installed docker compose by default for you. In case there is any issue, docker compose may be able to be installed by following:

```commandline

    # Create environment variable
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}

    # Create holding directory
    mkdir -p $DOCKER_CONFIG/cli-plugins

    # <version> and <arch> may be replaced with any of your choosing.
    curl -SL https://github.com/docker/compose/releases/download/<version>/docker-compose-linux-<arch> -o $DOCKER_CONFIG/cli-plugins/docker-compose

    # Give permissions to execute the plugin
    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

    # Check version
    docker compose version
```

In case of any doubt, the presented resources may serve as a guide:

Docker installation: https://docs.docker.com/desktop/install/linux/ubuntu/

Docker compose plugin installation: https://docs.docker.com/compose/install/linux/#install-the-plugin-manually

#### Install basic services

In order to process tasks asynchronously, a message queue needs to be instanced.
The dependencies were already during previous steps but it's still necessary to
run a redis server to set up the broker.

To easily install the basic services needed to run the application, we will make use of docker. To install them simply run:


```commandline

    # Start services
    docker compose -f docker-compose.yml up

```

Or, alternatively, create the containers manually:

```commandline
    docker run -d --name redis-backend -p 6379:6379 redis
    docker run -d --hostname rabbit-broker --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
    docker run --name chromadb --rm -p 8000:8000 chromadb/chroma
    docker run --name langchain-executor -p 5001:5001  jhuguet/langchain-executor
```


### Server Running Configurations

To comfortably host the application, the need of defining a server configuration strategy which manages multi threading and concurrency, an event driven architecture was defined, as well as the use of message brokers.

The tools to use are, on the server side, gunicorn. On the events and message broker side of things, RabbitMQ.

The next sections will be about running the servers based on a default configuration.

#### Run gunicorn as a server

Having already installed the required dependencies, in order to configure gunicorn as a server
it is only needed to run the following:

```commandline

    # Run from root directory
    gunicorn -c chroma/gunicorn.conf.py 'chroma:create_app()'
    
    # Run from root directory
    gunicorn -c user_langchain/gunicorn.conf.py 'user_langchain:create_app()'
```

#### Start Celery Application to process tasks

Now that we have our Flask application up and running, we need the celery application correspondent to each
Flask application in order for us to be able to process our tasks. 

In order for us to run our Celery applications, we must run the following commands:

```commandline
    
    # Run from a separate terminal each, at root level
    celery -A chroma worker --loglevel=info --time-limit=50 --soft-time-limit=30 -Q chroma_queue
    celery -A user_langchain worker --loglevel=debug --time-limit=50 --soft-time-limit=30 -Q langchain_queue

```


**Take into consideration:** The langchain and chromadb are both coupled and dependant on the redis, rabbit, and chroma services. In case of manually running the architecture, take into account that the services booted first.

#### Quick Server Setups

Alternatively, instead of running multiple terminals to start each server, the following commands can be executed:

```commandline

    # Run at root level at a separate terminal each
    sh chroma/initialize_chroma_services.sh
    
    sh user_langchain/initialize_langchain_services.sh

```

### Architecture bootup example:

To run the complete architecture easily, follow the next steps:

```commandline

    # Should run chromadb, rabbitmq, redis, langchain-executor
    sh bash_files/initialize_basic_services.sh

    # Should run the chroma-executor
    sh chroma/initialize_chroma_services.sh

```

Alternatively, you may also boot the whole architecture by executing: 


```commandline

    sh bash_files/bootup_architecture.sh

```

### CURLS EXAMPLES:

```
# EMBED A DOCUMENT INTO THE DATABASE BASED ON LOCAL SYSTEM FILE PATH

curl -X POST 'http://localhost:5000/chroma/embed_document' -H 'Content-Type: application/json' -d '{"collection_name": "some_collection", "categories": ["quimica"], "file_path": "sample_documents/chemistry_sample.pdf"}'

curl -X POST 'http://localhost:5000/chroma/embed_document' -H 'Content-Type: application/json' -d '{"collection_name": "some_collection", "categories": ["electronica"], "file_path": "sample_documents/tdg_sample.pdf"}'


curl -X POST 'http://localhost:5000/chroma/embed_document' -H 'Content-Type: application/json' -d '{"collection_name": "some_collection", "categories": ["quimica", "control"], "file_path": "/home/jupyter-juan_huguet82191/pdfSources/media/jairo/AlejandriaVault/Alejandria/Jutta Heckhausen/Motivation and Action (8620)/Motivation and Action - Jutta Heckhausen.pdf"}'

curl -X POST 'http://localhost:5000/chroma/embed_document' -H 'Content-Type: application/json' -d '{"collection_name": "some_collection", "categories": ["quimica", "control"], "file_path": "/home/jupyter-juan_huguet82191/pdfSources/media/jairo/AlejandriaVault/Alejandria/J. van Mill/Open Problems in Topology (4217)/Open Problems in Topology - J. van Mill.pdf"}'

curl -X POST 'http://localhost:5000/chroma/embed_document' -H 'Content-Type: application/json' -d '{"collection_name": "some_collection", "categories": ["informatica"], "file_path": "/home/jupyter-juan_huguet82191/pdfSources/media/jairo/AlejandriaVault/Alejandria/Jurgen Ackermann/Sampled-Data Control Systems_ Analysis and Synthesis, Robust System Design (3669)/Sampled-Data Control Systems_ Analysis and - Jurgen Ackermann.pdf"}'

# QUERY FILES IN DATABASE SERVER

curl -X POST 'http://localhost:5000/chroma/documents' -H 'Content-Type: application/json' -d '{"collection_name": "some_collection", "category": "quimica", "user_query": "hydrogenation"}'

curl -X POST 'http://localhost:5000/chroma/documents' -H 'Content-Type: application/json' -d '{"collection_name": "some_collection", "category": "quimica", "user_query": "What is an action?"}'
```
