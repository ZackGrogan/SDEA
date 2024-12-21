@echo off
SETLOCAL

echo Starting SEC Data Application and Test API

REM Set the project root directory
cd /d "%~dp0\.."

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
)

REM Install dependencies
pip install -r requirements.txt

REM Set Flask environment variables
set FLASK_APP=app\main.py
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Start the main application
start flask run --host=0.0.0.0 --port=5000 --reload

REM Start the test API
start python -m api.test_api --host=0.0.0.0 --port=5001

PAUSE
