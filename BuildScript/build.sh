#!/bin/bash

# Initial version
IMAGE_VERSION=0.3.18

echo "Building MoCab framework image for arm64..."
echo "Version: ${IMAGE_VERSION}"
echo ""

docker buildx build --platform linux/arm64 -t mocab-framework:${IMAGE_VERSION} -f BuildScript/Dockerfile --load .

docker run -d -p 0.0.0.0:5050:5000 --name mocab-framework mocab-framework:${IMAGE_VERSION}

# Extract the current version numbers
MAJOR=$(echo "$IMAGE_VERSION" | cut -d. -f1)
MINOR=$(echo "$IMAGE_VERSION" | cut -d. -f2)
PATCH=$(echo "$IMAGE_VERSION" | cut -d. -f3)

# Increment the patch version
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"

# Use sed to replace the IMAGE_VERSION in the script file
sed -i "" "s/IMAGE_VERSION=${IMAGE_VERSION}/IMAGE_VERSION=${NEW_VERSION}/" ./BuildScript/build.sh

echo "Updated version number to ${NEW_VERSION} in the script."
