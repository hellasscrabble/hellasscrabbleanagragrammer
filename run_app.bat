@echo off
cd /d "%~dp0"
python app.py
if errorlevel 1 (
    echo.
    echo Η εφαρμογή σταμάτησε λόγω σφάλματος. Διάβασε το μήνυμα παραπάνω.
    pause
)
