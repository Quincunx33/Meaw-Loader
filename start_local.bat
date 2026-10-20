@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 goto :error
)

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --upgrade -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Meaw Loader is starting. Open http://127.0.0.1:8080 in your browser.
echo Keep this window open while using the downloader. Press Ctrl+C to stop it.
echo.
".venv\Scripts\python.exe" server.py
goto :end

:error
echo.
echo Could not start Meaw Loader. Install Python 3.10 or newer and try again.
pause

:end
endlocal
