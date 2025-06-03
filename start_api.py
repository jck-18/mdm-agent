#!/usr/bin/env python3
"""
Cross-platform startup script for the MDM Agent API server
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_venv():
    """Setup and activate virtual environment"""
    venv_path = Path(".venv")
    
    # Create venv if it doesn't exist
    if not venv_path.exists():
        print("Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to create virtual environment: {e}")
            print("Trying alternative method...")
            subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv_path)], check=True)
    
    # Get the path to the Python executable in the venv
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    
    if not python_path.exists():
        print(f"Error: Virtual environment Python not found at {python_path}")
        sys.exit(1)
    
    return str(python_path)

def recreate_venv():
    """Delete and recreate virtual environment"""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("Removing corrupted virtual environment...")
        shutil.rmtree(venv_path)
    
    print("Creating fresh virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    
    # Get the path to the Python executable in the venv
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    
    return str(python_path)

def install_requirements(python_path):
    """Install required packages"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("Error: requirements.txt not found")
        sys.exit(1)
    
    # First ensure pip is available
    print("Ensuring pip is available...")
    try:
        subprocess.run([python_path, "-m", "ensurepip", "--upgrade"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Warning: ensurepip failed, pip might already be available")
    
    # Upgrade pip to latest version
    print("Upgrading pip...")
    try:
        subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to upgrade pip: {e}")
    
    print("Installing requirements...")
    subprocess.run([python_path, "-m", "pip", "install", "-r", str(requirements_file)], check=True)

def start_api_server(python_path):
    """Start the API server"""
    api_script = Path("api") / "app.py"
    if not api_script.exists():
        print(f"Error: API script not found at {api_script}")
        sys.exit(1)
    
    print("Starting API server...")
    subprocess.run([python_path, str(api_script)], check=True)

if __name__ == "__main__":
    # Get the project root directory
    project_root = Path(__file__).parent.resolve()
    os.chdir(project_root)
    
    try:
        # Setup virtual environment
        python_path = setup_venv()
          # Install requirements
        try:
            install_requirements(python_path)
        except subprocess.CalledProcessError:
            print("Failed to install requirements. Trying to recreate virtual environment...")
            python_path = recreate_venv()
            install_requirements(python_path)
        
        # Start API server
        start_api_server(python_path)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down API server...")
        sys.exit(0)