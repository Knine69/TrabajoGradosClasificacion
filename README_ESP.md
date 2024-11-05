## Proceso de configuración:


### Se requiere la versión de Python:

Este proyecto al día de hoy, requiere el uso de python 3.10.0 =<

#### Instalación de dependencias:

Para ejecutar una instalación de dependencia completa:

```commandline
    python -m venv .venv
    source .venv/bin/activate
    pip install -r chroma/requirements.txt
```

#### Crear archivo de configuración .env

Usando su editor de código preferido, cree un archivo `.env` que cargará variables de entorno en nuestras aplicaciones:

```text
# .env file
RABBIT_BROKER_URL=pyamqp://guest@localhost//
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CHROMA_QUEUE=chroma_queue
LANGCHAIN_QUEUE=langchain_queue
```

#### Instalación de Ollama

Para poder instalar Ollama, como usuario root el proceso es sencillo, simplemente ejecuta:

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

Si, por el contrario, deseas instalar ollama como usuario no root, sigue las siguientes instrucciones:

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

#### Instalar modelos LLM Ollama

Para obtener modelos optimizados creados para casos de uso de chat/diálogo:

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

Para instalar un modelo base previamente entrenado, ejecute:

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

Para comprobar si hay más modelos disponibles, consulte:

https://ollama.com/library

### Instalaciones de herramientas y servicios

#### Instalar la ventana acoplable


Es necesario instalar Docker para poder alojar los contenedores que expondrán los servicios y microservicios necesarios para la correcta ejecución de la aplicación. Siendo ese el caso, para poder utilizar Docker, sigue los siguientes pasos para instalar las herramientas necesarias:

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

El conjunto de comandos que se muestra antes debería haber instalado Docker Compose de forma predeterminada. En caso de que haya algún problema, es posible que Docker Compose pueda instalarse de la siguiente manera:

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

En caso de duda, los recursos presentados pueden servirle de guía:

Instalación de Docker: https://docs.docker.com/desktop/install/linux/ubuntu/

Instalación del complemento Docker Compose: https://docs.docker.com/compose/install/linux/#install-the-plugin-manually

#### Instalar servicios básicos

Para procesar tareas de forma asincrónica, es necesario crear una cola de mensajes.
Las dependencias ya estaban en los pasos anteriores pero aún es necesario
Ejecute un servidor Redis para configurar el corredor.

Para instalar fácilmente los servicios básicos necesarios para ejecutar la aplicación, utilizaremos Docker. Para instalarlos simplemente ejecute:


```commandline

    # Start services
    docker compose -f docker-compose.yml up

```

O, alternativamente, cree los contenedores manualmente:

```commandline
    docker run -d --name redis-backend -p 6379:6379 redis
    docker run -d --hostname rabbit-broker --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
    docker run --name chromadb --rm -p 8000:8000 chromadb/chroma
    docker run --name langchain-executor -p 5001:5001  jhuguet/langchain-executor
```


### Configuraciones en ejecución del servidor

Para alojar cómodamente la aplicación, se definió la necesidad de definir una estrategia de configuración del servidor que gestione multithreading y concurrencia, una arquitectura impulsada por eventos, así como el uso de brokers de mensajes.

Las herramientas a utilizar son, del lado del servidor, gunicorn. En el lado de los eventos y del corredor de mensajes, RabbitMQ.

Las siguientes secciones tratarán sobre la ejecución de los servidores según una configuración predeterminada.

#### Ejecute gunicorn como servidor

Habiendo ya instalado las dependencias requeridas, para poder configurar gunicorn como servidor
solo es necesario ejecutar lo siguiente:

```commandline

    # Run from root directory
    gunicorn -c chroma/gunicorn.conf.py 'chroma:create_app()'
    
    # Run from root directory
    gunicorn -c user_langchain/gunicorn.conf.py 'user_langchain:create_app()'
```

#### Inicie la aplicación Celery para procesar tareas

Ahora que tenemos nuestra aplicación Flask en funcionamiento, necesitamos la aplicación de apio correspondiente a cada
Aplicación Flask para que podamos procesar nuestras tareas. 

Para que podamos ejecutar nuestras aplicaciones de Celery, debemos ejecutar los siguientes comandos:

```commandline
    
    # Run from a separate terminal each, at root level
    celery -A chroma worker --loglevel=info --time-limit=50 --soft-time-limit=30 -Q chroma_queue
    celery -A user_langchain worker --loglevel=debug --time-limit=50 --soft-time-limit=30 -Q langchain_queue

```


**Tenga en cuenta:** Langchain y chromadb están acoplados y dependen de los servicios redis, Rabbit y chroma. En caso de ejecutar la arquitectura manualmente, tenga en cuenta que los servicios se iniciaron primero.

#### Configuraciones rápidas del servidor

Alternativamente, en lugar de ejecutar múltiples terminales para iniciar cada servidor, se pueden ejecutar los siguientes comandos:

```commandline

    # Run at root level at a separate terminal each
    sh chroma/initialize_chroma_services.sh
    
    sh user_langchain/initialize_langchain_services.sh

```

### Ejemplo de arranque de arquitectura:

Para ejecutar la arquitectura completa fácilmente, siga los siguientes pasos:

```commandline

    # Should run chromadb, rabbitmq, redis, langchain-executor
    sh bash_files/initialize_basic_services.sh

    # Should run the chroma-executor
    sh chroma/initialize_chroma_services.sh

```

Alternativamente, también puedes iniciar toda la arquitectura ejecutando:


```commandline

    sh bash_files/bootup_architecture.sh

```

### EJEMPLOS DE CURLS:

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
