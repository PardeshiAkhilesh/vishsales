@echo off
echo ========================================
echo Starting Vishal Sales Backend Server
echo ========================================
echo.

cd backend

echo Installing dependencies...
pip install -r app\requirements.txt

echo.
echo Starting FastAPI server on port 8000...
echo API Documentation: http://localhost:8000/docs
echo.

python -m uvicorn app.main:app --reload --port 8000
