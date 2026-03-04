@echo off
REM ========================================
REM   CityTransit - Limpiar Contenedores
REM ========================================
echo.
echo ========================================
echo   Limpiando Contenedores Docker
echo ========================================
echo.

cd citytransit-backend

echo Deteniendo y eliminando contenedores...
docker-compose -f docker-compose-database.yml down -v

echo.
echo Eliminando contenedores huerfanos...
docker container prune -f

echo.
echo Contenedores actuales:
docker ps -a

echo.
echo ========================================
echo   Limpieza Completada
echo ========================================
echo.
echo Ahora puedes ejecutar: INICIAR-TODO.bat
echo.
pause
