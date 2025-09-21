#!/bin/bash

CONTAINER_NAME="tg-bot-shemcar"

# Stop and remove the container if it exists
if [ "$(docker ps -aq -f name=^${CONTAINER_NAME}$)" ]; then
    echo "Stopping and removing existing container: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

# Build the Docker image
echo "Building Docker image: $CONTAINER_NAME"
docker build -t "$CONTAINER_NAME" .

# Run the Docker container
echo "Running Docker container: $CONTAINER_NAME"
docker run -d --name "$CONTAINER_NAME" "$CONTAINER_NAME"
