## Setup Process:

#### Resource installation:
```
    Need to install C++ build tools for chromadb. Follow resource: 

    https://visualstudio.microsoft.com/es/visual-cpp-build-tools/
```

### Python version required:

This project as of today, requires the use of python 3.9.13


#### Dependencies installation:

In order to solve possible issues that may arise, run the following dependencies installation:

Download Ollama and pull model to use locally

```
    pip torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install --upgrade pymupdf
```

For a whole dependency installation run:

```
    pip install -r requirements.txt
```


#### CURLS EXAMPLES:

```
# EMBED A DOCUMENT INTO THE DATABASE BASED ON LOCAL SYSTEM FILE PATH
curl -X POST 'http://localhost:5000/chroma/embed_document' -H 'Content-Type: application/json' -d '{"collection_name": "some_collection", "categories": ["quimica", "control"], "file_path": "chroma/sample_documents/chemistry_sample.pdf"}'

# QUERY FILES IN DATABASE SERVER
curl -X GET 'http://localhost:5000/chroma/documents' -H 'Content-Type: application/json' -d '{"collection_name": "some_collection", "category": "quimica", "search_text": "hydrogenation"}'
```
