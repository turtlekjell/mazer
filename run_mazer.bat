@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py webapp.py
) else (
  python webapp.py
)
if errorlevel 1 pause
