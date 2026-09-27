@echo off
REM ============================================================================
REM TFS-NS3 Telecom Digital Twin: Local Ceragon Lab Deployment Mode
REM ============================================================================
REM Connects to:
REM   - ETSI TeraFlowSDN at http://localhost:8088
REM   - Physical Ceragon MH-T261 (ctu-96) at 192.168.1.225:80
REM   - NS-3 Discrete Simulator at efid@cersrv-029 (/home/efid/ns3-dev/ns3)
echo.
echo ============================================================================
echo   Starting Local Ceragon Lab Telecom Digital Twin
echo   Coupled to Physical Hardware (192.168.1.225) + TFS (:8088) + NS-3 (cersrv-029)
echo ============================================================================
echo.
python web_dashboard.py --profile local-ceragon --port 9200
pause
