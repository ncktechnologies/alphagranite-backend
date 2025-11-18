#!/bin/bash

# Health check script for deployed application
# Tests if all services are running correctly

set -e

echo "=========================================="
echo "Alpha Granite Backend - Health Check"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# Check if Docker containers are running
echo ""
echo "Checking Docker containers..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Docker containers are running${NC}"
else
    echo -e "${RED}✗ Docker containers are not running${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check API health endpoint
echo ""
echo "Checking API health endpoint..."
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API health endpoint is responding${NC}"
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    echo "   Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ API health endpoint is not responding${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check if migrations ran successfully
echo ""
echo "Checking migration logs..."
if docker-compose logs web 2>/dev/null | grep -q "Auto Migration Completed Successfully"; then
    echo -e "${GREEN}✓ Migrations completed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Migration status unclear - check logs with: make logs${NC}"
fi

# Check disk space
echo ""
echo "Checking disk space..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓ Disk space OK ($DISK_USAGE% used)${NC}"
else
    echo -e "${YELLOW}⚠ Disk space usage high ($DISK_USAGE% used)${NC}"
fi

# Check memory usage
echo ""
echo "Checking memory usage..."
if command -v free &> /dev/null; then
    MEM_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100.0}' | cut -d. -f1)
    if [ "$MEM_USAGE" -lt 80 ]; then
        echo -e "${GREEN}✓ Memory usage OK ($MEM_USAGE% used)${NC}"
    else
        echo -e "${YELLOW}⚠ Memory usage high ($MEM_USAGE% used)${NC}"
    fi
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo "=========================================="
    exit 0
else
    echo -e "${RED}✗ $ERRORS check(s) failed${NC}"
    echo "=========================================="
    echo ""
    echo "Run 'make logs' to see detailed logs"
    exit 1
fi
