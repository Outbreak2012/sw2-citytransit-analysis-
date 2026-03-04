@echo off
REM ========================================
REM   CityTransit - Detener Todo el Sistema
REM ========================================
echo.
echo ========================================
echo   CityTransit - Deteniendo Sistema
echo ========================================
echo.

REM Detener bases de datos
echo [1/3] Deteniendo bases de datos Docker...
cd citytransit-backend
docker-compose -f docker-compose-database.yml down
echo OK - Bases de datos detenidas
echo.

REM Detener analytics (si existe)
echo [2/3] Deteniendo Analytics Service...
cd ..\analytics-service
if exist docker-compose.yml (
    docker-compose down
    echo OK - Analytics detenido
) else (
    echo Analytics no configurado con Docker
)
echo.

REM Matar procesos Java y Node.js
echo [3/3] Deteniendo procesos Backend y Frontend...

REM Detener procesos en puerto 8080 (Backend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
    echo Deteniendo proceso en puerto 8080 (PID: %%a)
    taskkill /PID %%a /F >nul 2>&1
)

REM Detener procesos en puerto 3000 (Frontend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo Deteniendo proceso en puerto 3000 (PID: %%a)
    taskkill /PID %%a /F >nul 2>&1
)

REM Detener procesos en puerto 8000 (Analytics)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Deteniendo proceso en puerto 8000 (PID: %%a)
    taskkill /PID %%a /F >nul 2>&1
)

echo OK - Procesos detenidos
echo.

echo ========================================
echo   SISTEMA DETENIDO COMPLETAMENTE
echo ========================================
echo.
echo Verificar contenedores Docker:
docker ps
echo.
pause
