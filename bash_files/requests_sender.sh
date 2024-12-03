#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <input_file>"
  exit 1
fi

input_file="$1"
collection="gaunal_collection"
values=("quimica" "control" "electronica" "mecanica" "electrica" "robotica")

if [ ! -f "$input_file" ]; then
  echo "Error: File '$input_file' not found."
  exit 1
fi

while IFS= read -r path; do
  curl -X POST 'http://192.168.0.71:5000/chroma/embed_document' \
    -H 'Content-Type: application/json' \
    -d "{\"collection_name\": \"$collection\", \"categories\": [\"${values[$RANDOM % ${#values[@]}]}\"], \"file_path\": \"$path\"}"

  echo
done < "$input_file"
