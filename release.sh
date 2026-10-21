#!/bin/env bash

set -e

if [[ -z "$VIRTUAL_ENV" ]]; then
    source venv/Scripts/activate
fi

# DONE - Fetch tags and get the latest one
git fetch --tags
version=$(git describe --tags $(git rev-list --tags --max-count=1))
version_number="${version#v}"  # Remove 'v' prefix if the tag has it
echo "Version: $version_number"

# Extract major, minor, and patch versions
IFS='.' read -r MAJOR_VERSION MINOR_VERSION PATCH_VERSION <<< "$version_number"
export MAJOR_VERSION MINOR_VERSION PATCH_VERSION
echo "Major version: $MAJOR_VERSION"
echo "Minor version: $MINOR_VERSION"
echo "Patch version: $PATCH_VERSION"

# Write version file
envsubst < version_file.txt > version_file.tmp
mv version_file.tmp version_file.txt
cat version_file.txt

# Install dependencies
pip install -r requirements.txt

# Lint with pylint
#pylint zip_bot.py

# Test with pytest
#pytest zip_bot.py

# Build executable with pyinstaller
pyinstaller --clean \
        -n zip_bot \
        --icon zip_bot.ico \
        --version-file version_file.txt \
        --onefile zip_bot.py

# Restore files with sensible data
cp .env .env.bak
git restore .env

# Create a release on GitHub
gh release create \
        $version --verify-tag \
        --notes-file release_notes.md \
        --title "ZIP_BOT release ${version}" \
        dist/zip_bot.exe

# Reverting placeholder files
git restore version_file.txt
