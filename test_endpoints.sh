#!/bin/bash

# Simple API endpoint validation script using curl

BASE_URL="http://localhost:8000"
API_URL="${BASE_URL}/api/v1"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

echo ""
echo "=========================================="
echo "API ENDPOINT VALIDATION"
echo "=========================================="
echo ""

test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=${4:-200}
    
    local url="${API_URL}${endpoint}"
    
    if [ "$method" = "GET" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$url")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" -H "Content-Type: application/json")
    fi
    
    if [ "$status" = "$expected_status" ] || [ "$status" = "401" ] || [ "$status" = "403" ]; then
        echo -e "${GREEN}✓${NC} $description: HTTP $status"
        ((passed++))
    else
        echo -e "${RED}✗${NC} $description: Expected $expected_status, got HTTP $status"
        ((failed++))
    fi
}

echo "Testing basic endpoints..."
echo ""

# Health check
test_endpoint "GET" "/../health" "Health check" "200"

# Resource endpoints
test_endpoint "GET" "/accounts" "List accounts"
test_endpoint "GET" "/stone-thickness" "List stone thickness"
test_endpoint "GET" "/stone-colors" "List stone colors"
test_endpoint "GET" "/stone-types" "List stone types"
test_endpoint "GET" "/edges" "List edges"
test_endpoint "GET" "/fab-types" "List fab types"

# Job and fab endpoints
test_endpoint "GET" "/jobs" "List jobs"
test_endpoint "GET" "/fabs" "List fabs"

# New endpoints
test_endpoint "GET" "/table-names" "Get table names"
test_endpoint "GET" "/jobs-with-fabs" "List jobs with fabs"
test_endpoint "GET" "/clockwork" "List clockwork entries"

echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $passed"
echo -e "${RED}Failed:${NC} $failed"
echo "Total: $((passed + failed))"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All accessible endpoints are working!${NC}"
    exit 0
else
    echo -e "${YELLOW}Note: Some failures may be due to auth requirements${NC}"
    exit 1
fi
