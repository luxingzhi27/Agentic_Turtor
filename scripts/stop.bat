@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app.ps1" stop
endlocal
