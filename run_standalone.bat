@echo off
REM ============================================================================
REM TFS-NS3 Telecom Digital Twin: Standalone Mode (Zero Dependencies)
REM ============================================================================
REM Runs completely in-memory using bundled 6G transport descriptors.
REM Safe to run anywhere without access to Ceragon hardware, VPN, or remote hosts.
echo.
echo ============================================================================
echo   Starting Standalone Telecom Digital Twin (0 External Dependencies)
echo ============================================================================
echo.
python web_dashboard.py --profile standalone --port 9200
pause
