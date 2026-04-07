@echo off
setlocal

echo ================================================
echo Starting NeurowellCA Backend Dev Server
echo ================================================
echo.

pushd backend
python -m uvicorn src.api.main:app --app-dir . --reload --host 0.0.0.0 --port 8000
set "EXIT_CODE=%ERRORLEVEL%"
popd

echo.
echo Backend stopped with exit code %EXIT_CODE%.
pause
