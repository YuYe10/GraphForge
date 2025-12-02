#!/bin/bash
# LunarInsight API startup script
# Usage: ./start-api.sh

echo "========================================"
echo "  LunarInsight API startup script"
echo "========================================"
echo ""

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found, creating..."
    python -m venv venv
    echo "Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
echo "Checking dependencies..."
if python -c "import fastapi" 2>/dev/null; then
    requirements_installed=true
else
    requirements_installed=false
fi

if [ "$requirements_installed" = false ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "Dependencies installed"
fi

# Ensure uploads directory exists
if [ ! -d "uploads" ]; then
    echo "Creating uploads directory..."
    mkdir -p uploads
    echo "Uploads directory created"
fi

echo ""
echo "Starting API service..."
echo "API address: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start service
uvicorn main:app --reload --host 0.0.0.0 --port 8000