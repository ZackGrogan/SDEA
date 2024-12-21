@echo off
echo Setting up virtual environment for SEC Data Application
cd %~dp0..

REM Check if venv already exists
if not exist "venv" (
    python -m venv venv
)

REM Activate virtual environment and install requirements
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo Virtual environment setup and requirements installed successfully.
pause
