#!/bin/bash

# Deployment script for Alpha Granite Backend
# This script should be run on the server after pulling the code

set -e

echo "=========================================="
echo "Alpha Granite Backend Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found!${NC}"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo -e "${RED}✗ Please update .env file with your production values before continuing!${NC}"
    echo "Edit .env file and run this script again."
    exit 1
fi

echo -e "${GREEN}✓ .env file found${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed!${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p static/uploads static/defaults logs nginx/ssl

echo -e "${GREEN}✓ Directories created${NC}"

# Stop existing containers
echo "Stopping existing containers (if any)..."
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true

echo -e "${GREEN}✓ Stopped existing containers${NC}"

# Build and start containers
echo "Building and starting containers..."
echo "This may take a few minutes on first run..."

if docker-compose up -d --build 2>/dev/null; then
    echo -e "${GREEN}✓ Containers started successfully (docker-compose)${NC}"
elif docker compose up -d --build 2>/dev/null; then
    echo -e "${GREEN}✓ Containers started successfully (docker compose)${NC}"
else
    echo -e "${RED}✗ Failed to start containers${NC}"
    exit 1
fi

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Check if services are running
if docker-compose ps 2>/dev/null | grep -q "Up" || docker compose ps 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}✓ Services are running${NC}"
else
    echo -e "${RED}✗ Services failed to start${NC}"
    echo "Checking logs..."
    docker-compose logs --tail=50 || docker compose logs --tail=50
    exit 1
fi

# Show running containers
echo ""
echo "=========================================="
echo "Running Containers:"
echo "=========================================="
docker-compose ps 2>/dev/null || docker compose ps 2>/dev/null

# Show application logs
echo ""
echo "=========================================="
echo "Application Logs (last 20 lines):"
echo "=========================================="
docker-compose logs --tail=20 web 2>/dev/null || docker compose logs --tail=20 web 2>/dev/null

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Application is running at:"
echo "  - API: http://localhost:8000"
echo "  - Nginx: http://localhost (if enabled)"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f web"
echo "  - Stop: docker-compose down"
echo "  - Restart: docker-compose restart"
echo "  - Rebuild: docker-compose up -d --build"
echo ""
echo "Database is running at:"
echo "  - Host: localhost"
echo "  - Port: 5432"
echo "  - Database: alpha_granite"
echo ""
