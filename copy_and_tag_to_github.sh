#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <github_repo_url> <tag>"
    exit 1
fi

# Assign arguments to variables
GITHUB_REPO_URL=$1
TAG=$2

# Configure Git with your GitHub credentials
git config --global user.email "nathalie.giraudon@nesi.org.nz" #if it works needs to change to general user
git config --global user.name "natnesi"

# Add the GitHub repository as a remote
git remote add github $GITHUB_REPO_URL

# Push the specified tag to the GitHub repository
git push github main --force

# Tag the latest commit on GitHub with the specified tag
git tag -a "$TAG" -m "Tagging commit with $TAG"
git push github --tags

echo "Tag $TAG pushed and applied to the latest commit in GitHub repository $GITHUB_REPO_URL"