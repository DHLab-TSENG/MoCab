#!/bin/bash

# Initial version
echo "Building MoCab framework image for arm64..."
docker buildx build --platform linux/arm64 -t mocab-framework:${IMAGE_VERSION} -f BuildScript/Dockerfile --load .
