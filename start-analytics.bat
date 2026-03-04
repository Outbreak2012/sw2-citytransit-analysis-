@echo off
echo ========================================
echo   Analytics Service - Iniciando
echo ========================================
echo.

cd /d "%~dp0"

echo Verificando Python...
python --version

echo.
echo Creando entorno virtual...
if not exist "venv" (
    python -m venv venv
)

echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo.
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Iniciando servicio Analytics...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
