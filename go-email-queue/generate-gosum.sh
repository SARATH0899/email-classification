#!/bin/bash
# Script to generate correct go.sum file

echo "Generating correct go.sum file..."

# Clean module cache
go clean -modcache

# Remove existing go.sum if it exists
rm -f go.sum

# Tidy modules and download dependencies
go mod tidy
go mod download
go mod verify

echo "go.sum generated successfully!"
