@echo off
REM ========================================
REM   CityTransit - Script de Verificacion
REM ========================================
echo.
echo ========================================
echo   CityTransit - Verificacion del Sistema
echo ========================================
echo.

echo [Verificando Requisitos]
echo.

REM Docker
echo Verificando Docker...
docker --version
if errorlevel 1 (
    echo [X] Docker NO instalado
) else (
    echo [OK] Docker instalado
)
echo.

REM Java
echo Verificando Java...
java -version
if errorlevel 1 (
    echo [X] Java NO instalado
) else (
    echo [OK] Java instalado
)
echo.

REM Node.js
echo Verificando Node.js...
node --version
if errorlevel 1 (
    echo [X] Node.js NO instalado
) else (
    echo [OK] Node.js instalado
)
echo.

REM npm
echo Verificando npm...
npm --version
if errorlevel 1 (
    echo [X] npm NO instalado
) else (
    echo [OK] npm instalado
)
echo.

REM Python (opcional)
echo Verificando Python (opcional)...
python --version 2>nul
if errorlevel 1 (
    echo [!] Python NO instalado (opcional para Analytics)
) else (
    echo [OK] Python instalado
)
echo.

echo ========================================
echo [Verificando Servicios]
echo.

REM Contenedores Docker
echo Contenedores Docker en ejecucion:
docker ps
echo.

REM Backend
echo Verificando Backend (puerto 8080)...
curl -s http://localhost:8080/actuator/health >nul 2>&1
if errorlevel 1 (
    echo [X] Backend NO responde en http://localhost:8080
) else (
    echo [OK] Backend funcionando en http://localhost:8080
    curl http://localhost:8080/actuator/health
)
echo.

REM Frontend
echo Verificando Frontend (puerto 3000)...
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [X] Frontend NO responde en http://localhost:3000
) else (
    echo [OK] Frontend funcionando en http://localhost:3000
)
echo.

REM Analytics
echo Verificando Analytics (puerto 8000)...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [!] Analytics NO responde en http://localhost:8000 (opcional)
) else (
    echo [OK] Analytics funcionando en http://localhost:8000
)
echo.

echo ========================================
echo [Verificando Puertos]
echo.

echo Puerto 3000 (Frontend):
netstat -ano | findstr :3000 | findstr LISTENING
echo.

echo Puerto 8080 (Backend):
netstat -ano | findstr :8080 | findstr LISTENING
echo.

echo Puerto 5432 (PostgreSQL):
netstat -ano | findstr :5432 | findstr LISTENING
echo.

echo Puerto 27017 (MongoDB):
netstat -ano | findstr :27017 | findstr LISTENING
echo.

echo Puerto 6379 (Redis):
netstat -ano | findstr :6379 | findstr LISTENING
echo.

echo ========================================
echo   Verificacion Completada
echo ========================================
echo.
pause
