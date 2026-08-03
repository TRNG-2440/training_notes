@echo off

cd /d "%~dp0"

echo Starting SQL Server Windows Authentication Bridge...
echo.

powershell.exe ^
  -NoProfile ^
  -ExecutionPolicy Bypass ^
  -File "%~dp0sql_bridge.ps1"

pause