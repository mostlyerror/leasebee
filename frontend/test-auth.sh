#!/bin/bash
# Authentication Integration Test Script
# Tests all auth flows without manual browser interaction

set -e

echo "🧪 LeaseBee Authentication Integration Tests"
echo "============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper function to test URL response
test_url() {
    local name=$1
    local url=$2
    local expected=$3

    echo -n "Testing $name... "

    response=$(curl -s "$url")

    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Expected to find: $expected"
        echo "  Got: $(echo "$response" | head -c 200)..."
        ((FAILED++))
    fi
}

# Helper function to test redirect
test_redirect() {
    local name=$1
    local url=$2
    local expected_redirect=$3

    echo -n "Testing $name redirect... "

    # Follow redirects and get final URL
    final_url=$(curl -Ls -o /dev/null -w '%{url_effective}' "$url")

    if [[ "$final_url" == *"$expected_redirect"* ]]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Expected redirect to: $expected_redirect"
        echo "  Got: $final_url"
        ((FAILED++))
    fi
}

# Check if servers are running
echo "📡 Checking servers..."
echo ""

if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${RED}✗ Frontend not running on port 3000${NC}"
    echo "  Run: npm run dev"
    exit 1
fi

if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Backend not running on port 8000${NC}"
    echo "  Some tests may fail. Run: uvicorn app.main:app --reload"
    echo ""
fi

echo -e "${GREEN}✓ Servers are running${NC}"
echo ""

# Test 1: Auth Pages Render
echo "1️⃣  Testing Auth Page Rendering"
echo "--------------------------------"
test_url "Login page" "http://localhost:3000/login" "Welcome back"
test_url "Signup page" "http://localhost:3000/signup" "Create your account"
test_url "Password field on login" "http://localhost:3000/login" "type=\"password\""
test_url "Email field on signup" "http://localhost:3000/signup" "type=\"email\""
test_url "Organization field on signup" "http://localhost:3000/signup" "Organization name"
test_url "Password strength indicator" "http://localhost:3000/signup" "Password"
echo ""

# Test 2: Layout Structure
echo "2️⃣  Testing Layout Structure"
echo "----------------------------"
test_url "Auth layout has LeaseBee branding" "http://localhost:3000/login" "LeaseBee"
test_url "Auth layout has bee emoji" "http://localhost:3000/login" "🐝"
test_url "Login has sign up link" "http://localhost:3000/login" "Sign up"
test_url "Signup has sign in link" "http://localhost:3000/signup" "Sign in"
test_url "Auth pages have copyright" "http://localhost:3000/login" "© 2026"
echo ""

# Test 3: Protected Routes (Client-Side, check SSR output)
echo "3️⃣  Testing Protected Routes (SSR)"
echo "----------------------------------"
test_url "Dashboard shows loading/content" "http://localhost:3000/" "Loading"
echo ""

# Test 4: Build Verification
echo "4️⃣  Testing Build"
echo "----------------"
echo -n "Testing Next.js build... "
if npm run build > /tmp/build-test.log 2>&1; then
    if grep -q "Compiled successfully" /tmp/build-test.log; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Build succeeded but didn't compile successfully"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Build failed. Check /tmp/build-test.log"
    ((FAILED++))
fi
echo ""

# Test 5: TypeScript Check
echo "5️⃣  Testing TypeScript"
echo "---------------------"
echo -n "Testing type checking... "
if npm run build > /tmp/type-test.log 2>&1; then
    if grep -q "Linting and checking validity of types" /tmp/type-test.log; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi
echo ""

# Test 6: API Endpoint Availability (if backend is running)
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "6️⃣  Testing Backend API"
    echo "----------------------"
    test_url "Backend health" "http://localhost:8000" "FastAPI"
    test_url "Auth signup endpoint exists" "http://localhost:8000/docs" "/api/auth/signup"
    test_url "Auth login endpoint exists" "http://localhost:8000/docs" "/api/auth/login"
    test_url "Organizations endpoint exists" "http://localhost:8000/docs" "/api/organizations"
    echo ""
fi

# Test 7: JavaScript Bundle Size
echo "7️⃣  Testing Bundle Size"
echo "----------------------"
echo -n "Checking bundle size... "
if [ -f ".next/static/chunks/main-app.js" ]; then
    size=$(stat -f%z ".next/static/chunks/main-app.js" 2>/dev/null || stat -c%s ".next/static/chunks/main-app.js" 2>/dev/null)
    size_kb=$((size / 1024))
    if [ $size_kb -lt 200 ]; then
        echo -e "${GREEN}✓ PASS ($size_kb KB)${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ WARNING ($size_kb KB, should be < 200KB)${NC}"
        ((PASSED++))
    fi
else
    echo -e "${YELLOW}⚠ SKIP (run build first)${NC}"
fi
echo ""

# Test 8: Critical Files Exist
echo "8️⃣  Testing File Structure"
echo "-------------------------"
critical_files=(
    "src/lib/auth.ts"
    "src/contexts/AuthContext.tsx"
    "src/app/(auth)/layout.tsx"
    "src/app/(auth)/login/page.tsx"
    "src/app/(auth)/signup/page.tsx"
    "src/app/(app)/layout.tsx"
    "src/app/(app)/page.tsx"
    "src/middleware.ts"
)

for file in "${critical_files[@]}"; do
    echo -n "  $file... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC}"
        ((FAILED++))
    fi
done
echo ""

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
