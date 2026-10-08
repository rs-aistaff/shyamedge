@echo off
echo Starting ShyamEdge FastAPI Telemetry Server on http://localhost:8000 ...
python -m uvicorn api.main:app --reload --port 8000
pause
