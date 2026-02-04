#!/bin/bash
# Quick script to trigger extraction for lease 26

# Get the token from your browser's localStorage
# Run this in browser console first: localStorage.getItem('leasebee_access_token')
# Then paste the token here:

TOKEN="${1:-your_token_here}"

echo "Triggering extraction for lease 26..."
curl -X POST "http://localhost:8000/api/extractions/extract/26" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

echo -e "\n\nExtraction started! Go to http://localhost:3000/review/26 to see the progress."
