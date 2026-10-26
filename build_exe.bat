@echo off
call .venv\Scripts\activate
pip install pyinstaller
pyinstaller --noconfirm --windowed --name RafaVideoStudioAI_V2 --collect-all PySide6 main.py
pause
