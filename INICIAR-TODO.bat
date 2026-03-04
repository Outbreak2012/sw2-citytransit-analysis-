@echo off
REM ========================================
REM   CityTransit - Iniciar Todo el Sistema
REM ========================================
echo.
echo ========================================
echo   CityTransit - Sistema Completo
echo ========================================
echo.
echo Este script iniciara:
echo   1. Bases de datos (PostgreSQL, MongoDB, Redis)
echo   2. Backend (Spring Boot en puerto 8080)
echo   3. Frontend (Next.js en puerto 3000)
echo.
echo Presiona Ctrl+C para cancelar o espera 5 segundos...
timeout /t 5
echo.

REM Verificar Docker
echo [1/6] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker no esta instalado o no esta en el PATH
    echo Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo OK - Docker instalado

REM Verificar que Docker Desktop este ejecutandose
docker ps >nul 2>&1
if errorlevel 1 (
    echo.
    echo ========================================
    echo   DOCKER DESKTOP NO ESTA EJECUTANDOSE
    echo ========================================
    echo.
    echo Por favor:
    echo   1. Abre Docker Desktop manualmente
    echo   2. Espera a que inicie completamente
    echo   3. Vuelve a ejecutar este script
    echo.
    echo Intentando abrir Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo.
    echo Esperando 30 segundos para que Docker Desktop inicie...
    timeout /t 30
    
    REM Verificar nuevamente
    docker ps >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Docker Desktop no inicio correctamente
        echo Por favor inicialo manualmente y vuelve a ejecutar este script
        pause
        exit /b 1
    )
)
echo OK - Docker Desktop ejecutandose
echo.

REM Verificar Java
echo [2/6] Verificando Java...
java -version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Java no esta instalado o no esta en el PATH
    echo Configurando JAVA_HOME...
    set "JAVA_HOME=C:\Users\Camilo Sarmiento\AppData\Roaming\Code\User\globalStorage\pleiades.java-extension-pack-jdk\java\21"
    set "PATH=%JAVA_HOME%\bin;%PATH%"
    "%JAVA_HOME%\bin\java.exe" -version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: No se pudo configurar Java
        echo Por favor instala Java 17+ desde: https://adoptium.net/
        pause
        exit /b 1
    )
)
echo OK - Java detectado
echo.

REM Verificar Node.js
echo [3/6] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no esta instalado o no esta en el PATH
    echo Por favor instala Node.js desde: https://nodejs.org/
    pause
    exit /b 1
)
echo OK - Node.js detectado
echo.

REM Iniciar bases de datos
echo [4/6] Iniciando bases de datos con Docker...
cd citytransit-backend

echo Deteniendo contenedores existentes si los hay...
docker-compose -f docker-compose-database.yml down >nul 2>&1

echo Iniciando bases de datos...
docker-compose -f docker-compose-database.yml up -d
if errorlevel 1 (
    echo.
    echo ERROR: No se pudieron iniciar las bases de datos
    echo.
    echo Intentando limpiar y reiniciar...
    docker-compose -f docker-compose-database.yml down -v
    timeout /t 5 /nobreak >nul
    docker-compose -f docker-compose-database.yml up -d
    if errorlevel 1 (
        echo ERROR: Aun no se pueden iniciar las bases de datos
        echo.
        echo Ejecuta manualmente:
        echo   cd citytransit-backend
        echo   docker-compose -f docker-compose-database.yml down -v
        echo   docker-compose -f docker-compose-database.yml up -d
        pause
        exit /b 1
    )
)
echo OK - Bases de datos iniciadas
echo.
echo Esperando 30 segundos para que las bases de datos esten listas...
timeout /t 30 /nobreak
echo.

REM Verificar si el JAR existe
echo [5/6] Verificando backend...
if not exist "target\citytransit-backend-1.0.0.jar" (
    echo El archivo JAR no existe. Compilando proyecto...
    call mvnw.cmd clean package -DskipTests
    if errorlevel 1 (
        echo ERROR: No se pudo compilar el backend
        pause
        exit /b 1
    )
)
echo OK - Backend compilado
echo.

REM Verificar node_modules
echo [6/6] Verificando frontend...
cd ..\citytransit-web
if not exist "node_modules" (
    echo Instalando dependencias del frontend...
    call npm install
    if errorlevel 1 (
        echo ERROR: No se pudieron instalar las dependencias del frontend
        pause
        exit /b 1
    )
)
echo OK - Frontend listo
echo.

echo ========================================
echo   INICIANDO SERVICIOS
echo ========================================
echo.
echo Abriendo terminales separadas para cada servicio...
echo.

REM Iniciar backend en nueva ventana
cd ..\citytransit-backend
start "CityTransit Backend" cmd /k "echo Iniciando Backend en puerto 8080... && start-backend.bat"

REM Esperar 10 segundos
echo Esperando 10 segundos para que el backend inicie...
timeout /t 10 /nobreak

REM Iniciar frontend en nueva ventana
cd ..\citytransit-web
start "CityTransit Frontend" cmd /k "echo Iniciando Frontend en puerto 3000... && npm run dev"

echo.
echo ========================================
echo   SISTEMA INICIADO
echo ========================================
echo.
echo URLs de acceso:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8080
echo   GraphiQL:  http://localhost:8080/graphiql
echo   Swagger:   http://localhost:8080/swagger-ui.html
echo   PgAdmin:   http://localhost:5050
echo.
echo Credenciales:
echo   Email:     admin@citytransit.com
echo   Password:  admin123
echo.
echo Presiona cualquier tecla para cerrar esta ventana.
echo Los servicios seguiran ejecutandose en sus propias ventanas.
pause
