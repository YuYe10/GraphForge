#!/bin/bash
# Bash script to start Vue frontend
echo "Starting LunarInsight Vue Frontend..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start dev server
echo "Starting development server on http://localhost:3000"
npm run dev