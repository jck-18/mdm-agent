#!/bin/bash
# MDM Agent API Startup Script

echo "=== MDM Agent REST API Startup ==="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment (Windows)
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
# Activate virtual environment (Unix)
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Warning: Could not find virtual environment activation script"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the API server
echo "Starting MDM Agent REST API..."
python app.py
