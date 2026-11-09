@echo off
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python3 "%~dp0runner.py" %*
) else (
    python "%~dp0runner.py" %*
)
