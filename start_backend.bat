@echo off
echo Installing Python dependencies...
pip install -r requirements.txt
echo Installing Playwright browsers...
playwright install chromium
echo Starting FastAPI backend on http://localhost:8000
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
