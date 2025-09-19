#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
GITHUB_REPO="unsafe9/alfred-gitopen" 
WORKFLOW_NAME="Git Open"
# List of files to include in the workflow package.
# It automatically includes all Python scripts.
FILES_TO_PACKAGE=(
    *.py
    info.plist
    icon.png
    README.md
)
# --- End of Configuration ---

# 1. Check for GitHub CLI
if ! command -v gh &> /dev/null
then
    echo "GitHub CLI (gh) could not be found."
    echo "Please install it to continue: https://cli.github.com/"
    exit 1
fi

# 2. Ask for the version
read -p "Enter the version for this release (e.g., 1.0.0): " VERSION
if [[ -z "$VERSION" ]]; then
    echo "Version number cannot be empty."
    exit 1
fi

TAG="v$VERSION"
PACKAGE_NAME="$WORKFLOW_NAME-$TAG.alfredworkflow"
BUILD_DIR="build"

echo "--------------------------------------------------"
echo "Preparing release for $WORKFLOW_NAME version $TAG"
echo "Repository: $GITHUB_REPO"
echo "Package: $PACKAGE_NAME"
echo "--------------------------------------------------"

# 3. Create a temporary build directory
echo "Creating build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# 4. Copy files to the build directory
echo "Copying workflow files..."
for file in "${FILES_TO_PACKAGE[@]}"; do
    cp "$file" "$BUILD_DIR/"
done

# 5. Create the .alfredworkflow package
echo "Creating .alfredworkflow package..."
(
    cd "$BUILD_DIR" || exit
    zip -r "../$PACKAGE_NAME" ./*
)

# 6. Create a new GitHub release
echo "Creating GitHub release..."
gh release create "$TAG" \
    --repo "$GITHUB_REPO" \
    --title "$WORKFLOW_NAME $TAG" \
    --generate-notes \
    "$PACKAGE_NAME"

# 7. Clean up
echo "Cleaning up..."
rm -rf "$BUILD_DIR"
rm "$PACKAGE_NAME"

echo "--------------------------------------------------"
echo "✅ Release $TAG created successfully!"
echo "--------------------------------------------------"
