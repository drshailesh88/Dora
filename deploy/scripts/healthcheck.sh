#!/bin/bash
# Health check script for Dora API
set -e

# Configuration
API_HOST="${API_HOST:-localhost}"
API_PORT="${API_PORT:-8000}"
HEALTH_ENDPOINT="http://${API_HOST}:${API_PORT}/health"
TIMEOUT=5

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local expected_status=${2:-200}

    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected_status" ]; then
        return 0
    else
        echo "ERROR: Health check failed. HTTP $response (expected $expected_status)"
        return 1
    fi
}

# Function to check service status
check_service_status() {
    local response=$(curl -s --max-time "$TIMEOUT" "$HEALTH_ENDPOINT" 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo "ERROR: Cannot connect to health endpoint"
        return 1
    fi

    # Parse JSON response (requires jq if available, otherwise basic check)
    if command -v jq &> /dev/null; then
        status=$(echo "$response" | jq -r '.status // empty')
        if [ "$status" != "healthy" ]; then
            echo "ERROR: Service status is not healthy: $status"
            return 1
        fi
    else
        # Basic check if jq is not available
        if ! echo "$response" | grep -q '"status".*"healthy"'; then
            echo "ERROR: Service does not report healthy status"
            return 1
        fi
    fi

    return 0
}

# Main health check
echo "Performing health check..."

# Check if endpoint is accessible
if ! check_http "$HEALTH_ENDPOINT" 200; then
    exit 1
fi

# Check service status
if ! check_service_status; then
    exit 1
fi

echo "Health check passed!"
exit 0
