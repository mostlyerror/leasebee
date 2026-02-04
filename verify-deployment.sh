#!/bin/bash
# LeaseBee Deployment Verification Script

set -e

echo "================================================"
echo "LeaseBee Deployment Verification"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check URL
check_url() {
    local url=$1
    local name=$2
    
    echo -n "Checking $name... "
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|301\|302"; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to check backend health
check_backend_health() {
    local backend_url=$1
    
    echo -n "Checking backend health endpoint... "
    response=$(curl -s "${backend_url}/health" || echo "failed")
    
    if echo "$response" | grep -q "healthy"; then
        echo -e "${GREEN}✓ OK${NC}"
        echo "   Response: $response"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "   Response: $response"
        return 1
    fi
}

# Function to check CORS
check_cors() {
    local backend_url=$1
    local frontend_url=$2
    
    echo -n "Checking CORS configuration... "
    response=$(curl -s -H "Origin: $frontend_url" -H "Access-Control-Request-Method: POST" -X OPTIONS "${backend_url}/api/auth/signup" -I || echo "failed")
    
    if echo "$response" | grep -q "access-control-allow-origin"; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ WARNING - CORS may not be configured${NC}"
        return 1
    fi
}

# Main verification
echo "This script will verify your Railway deployment."
echo ""

# Get URLs from user
read -p "Enter your backend URL (e.g., https://backend-production-xyz.up.railway.app): " BACKEND_URL
read -p "Enter your frontend URL (e.g., https://frontend-production-xyz.up.railway.app): " FRONTEND_URL

# Remove trailing slashes
BACKEND_URL=${BACKEND_URL%/}
FRONTEND_URL=${FRONTEND_URL%/}

echo ""
echo "================================================"
echo "Running Checks..."
echo "================================================"
echo ""

# Check backend
check_url "$BACKEND_URL" "Backend URL"
check_backend_health "$BACKEND_URL"

# Check frontend
check_url "$FRONTEND_URL" "Frontend URL"

# Check CORS
check_cors "$BACKEND_URL" "$FRONTEND_URL"

# Check database (via Railway CLI)
echo ""
echo -n "Checking database connection (via Railway CLI)... "
if railway run --service backend python -c "from app.database import engine; engine.connect(); print('OK')" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ Could not verify (Railway CLI may not be linked)${NC}"
fi

# Summary
echo ""
echo "================================================"
echo "Verification Complete"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Open $FRONTEND_URL in your browser"
echo "2. Log in with: admin@leasebee.com / changeme123"
echo "3. Change the admin password"
echo "4. Test uploading a lease document"
echo ""
echo "If any checks failed, review DEPLOY_NOW.md for troubleshooting."
