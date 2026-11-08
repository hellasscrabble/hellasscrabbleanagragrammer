@echo off
cd /d "%~dp0"
python preview_web.py
if errorlevel 1 (
    echo.
    echo Δεν ξεκίνησε η προεπισκόπηση. Διάβασε το μήνυμα παραπάνω.
    pause
)
