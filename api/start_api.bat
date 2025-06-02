@echo off
REM MDM Agent API Startup Script for Windows

echo === MDM Agent REST API Startup ===

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start the API server
echo Starting MDM Agent REST API...
python app.py

pause
