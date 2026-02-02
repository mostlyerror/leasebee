#!/bin/bash
# Verify Railway deployment is working

echo "🔍 LeaseBee Deployment Verification"
echo "===================================="
echo ""

# Check if URLs are provided
if [ -z "$1" ]; then
    echo "Usage: ./verify_deployment.sh <backend-url> <frontend-url>"
    echo "Example: ./verify_deployment.sh https://backend.railway.app https://frontend.railway.app"
    exit 1
fi

BACKEND_URL=$1
FRONTEND_URL=${2:-}

# Test backend health
echo "1. Testing Backend Health..."
echo "   URL: $BACKEND_URL/health"
HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "   ✅ Backend is healthy!"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "   ❌ Backend health check failed!"
    echo "   Response: $HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test backend API docs
echo "2. Testing API Documentation..."
echo "   URL: $BACKEND_URL/docs"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/docs")

if [ "$DOCS_STATUS" = "200" ]; then
    echo "   ✅ API docs accessible!"
else
    echo "   ❌ API docs not accessible (HTTP $DOCS_STATUS)"
fi
echo ""

# Test frontend if URL provided
if [ -n "$FRONTEND_URL" ]; then
    echo "3. Testing Frontend..."
    echo "   URL: $FRONTEND_URL"
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
    
    if [ "$FRONTEND_STATUS" = "200" ]; then
        echo "   ✅ Frontend is accessible!"
    else
        echo "   ❌ Frontend not accessible (HTTP $FRONTEND_STATUS)"
    fi
    echo ""
    
    # Test CORS
    echo "4. Testing CORS Configuration..."
    CORS_RESPONSE=$(curl -s -I -H "Origin: $FRONTEND_URL" "$BACKEND_URL/health" | grep -i "access-control-allow-origin")
    
    if [ -n "$CORS_RESPONSE" ]; then
        echo "   ✅ CORS configured!"
        echo "   Headers: $CORS_RESPONSE"
    else
        echo "   ⚠️  CORS headers not found (might need configuration)"
    fi
    echo ""
fi

echo "===================================="
echo "✅ Deployment verification complete!"
echo ""
echo "Next steps:"
echo "1. Login to $FRONTEND_URL"
echo "2. Create a test account"
echo "3. Upload a test PDF"
echo "4. Verify extraction works"
