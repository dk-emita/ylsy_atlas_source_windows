@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py run.py & exit /b)
python run.py
