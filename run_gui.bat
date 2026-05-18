@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" "TG Names Roller.pyw"
) else (
  start "" pythonw "TG Names Roller.pyw"
)
exit
