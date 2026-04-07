@echo off
echo Installing required Python packages...
echo.

cd /d "%~dp0"

echo Installing yfinance...
python -m pip install yfinance

echo.
echo Installing pandas...
python -m pip install pandas

echo.
echo Installing feedparser...
python -m pip install feedparser

echo.
echo Installing fastapi...
python -m pip install fastapi

echo.
echo Installing uvicorn...
python -m pip install uvicorn

echo.
echo Installing pydantic...
python -m pip install pydantic

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo You can now run: python main.py
echo.
pause
