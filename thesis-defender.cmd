@echo off
setlocal
cd /d "%~dp0\backend"
python -m cli.main %*
endlocal
