@echo off
REM ========================================
REM   Forzar Eliminacion de Contenedores
REM ========================================
echo.
echo Deteniendo y eliminando contenedores citytransit...
echo.

REM Detener todos los contenedores citytransit
echo [1/4] Deteniendo contenedores...
docker stop citytransit-postgres citytransit-pgadmin citytransit-mongodb citytransit-redis >nul 2>&1
docker stop citytransit-clickhouse >nul 2>&1

REM Eliminar contenedores
echo [2/4] Eliminando contenedores...
docker rm citytransit-postgres citytransit-pgadmin citytransit-mongodb citytransit-redis >nul 2>&1
docker rm citytransit-clickhouse >nul 2>&1

REM Limpiar contenedores huerfanos
echo [3/4] Limpiando contenedores huerfanos...
docker container prune -f

REM Verificar
echo [4/4] Contenedores restantes:
docker ps -a | findstr citytransit

echo.
echo ========================================
echo   Limpieza Completada
echo ========================================
echo.
echo Presiona cualquier tecla para continuar...
pause >nul

REM Ahora iniciar bases de datos
echo.
echo Iniciando bases de datos limpias...
cd citytransit-backend
docker-compose -f docker-compose-database.yml up -d

echo.
echo Bases de datos iniciadas!
echo.
pause
