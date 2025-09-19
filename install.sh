#!/bin/bash

# Simple Alfred workflow installer for development/testing
set -e

WORKFLOW_NAME="Git Open"
FILES_TO_PACKAGE=(*.py info.plist icon.png)
BUILD_DIR="build"
PACKAGE_NAME="$WORKFLOW_NAME.alfredworkflow"

# Check if we're in the project root directory
if [ ! -f "info.plist" ]; then
    echo "Error: info.plist not found. Run from project root directory."
    exit 1
fi

# Create build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy files to the build directory
for file in "${FILES_TO_PACKAGE[@]}"; do
    cp "$file" "$BUILD_DIR/"
done

# Create .alfredworkflow package
(
    cd "$BUILD_DIR" || exit
    zip -r "../$PACKAGE_NAME" ./*
)

# Install to Alfred
open "$PACKAGE_NAME"

# Clean up
rm -rf "$BUILD_DIR"

echo "Workflow installed. Check Alfred for import dialog."
