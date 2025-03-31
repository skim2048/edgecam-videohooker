#!/bin/bash
TAG="videohooker"
PARDIR="$(dirname "$(realpath "$0")")"
CONTAINER="$(basename "$PARDIR")"
docker run -it --net=host \
    --name $CONTAINER $TAG /bin/bash