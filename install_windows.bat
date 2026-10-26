@echo off
py -3.12 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Instale o FFmpeg se necessario: winget install Gyan.FFmpeg
echo Depois execute run_windows.bat
pause
