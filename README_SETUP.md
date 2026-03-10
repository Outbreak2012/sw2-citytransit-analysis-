# CityTransit / PayTransit — Guía de Instalación desde Cero

## Requisitos Previos

Instala el siguiente software antes de continuar:

| Software | Versión mínima | Descarga |
|---|---|---|
| Docker Desktop | 20.10+ | https://www.docker.com/products/docker-desktop |
| Java JDK | 21 | https://adoptium.net/ |
| Node.js | 18+ | https://nodejs.org/ |
| Git | cualquiera | https://git-scm.com/ |

> Asegúrate de que `java`, `node`, `npm` y `docker` estén disponibles en el PATH del sistema.

---

## Estructura del Proyecto

```
Segundo Parcial/
├── citytransit-backend/    # API REST + GraphQL (Spring Boot, Java 21, puerto 8080)
├── citytransit-web/        # Frontend (Next.js 14, puerto 3000)
└── analytics-service/      # Servicio de analytics y ML (Python/FastAPI, puerto 8001)
```

---

## Paso 1 — Levantar las Bases de Datos (Docker)

Abre una terminal en la carpeta `citytransit-backend` y ejecuta:

```bash
cd citytransit-backend
docker-compose up -d postgres mongodb redis clickhouse
```

Espera ~30 segundos y verifica que todos los contenedores estén **healthy**:

```bash
docker ps
```

Debes ver estos 4 contenedores en estado `healthy`:

| Contenedor | Puerto |
|---|---|
| paytransit-postgres | 5434 |
| paytransit-mongodb | 27017 |
| paytransit-redis | 6379 |
| paytransit-clickhouse | 8123, 9000 |

---

## Paso 2 — Levantar el Backend (Spring Boot)

### Opción A: Con Docker (recomendado, incluye compilación automática)

Desde la carpeta `citytransit-backend`:

```bash
docker-compose up -d --build backend
```

Espera ~60 segundos y verifica:

```bash
curl http://localhost:8080/actuator/health
# Debe responder: {"status":"UP", ...}
```

### Opción B: Con Maven local

```bash
cd citytransit-backend

# Compilar (solo la primera vez o tras cambios en el código)
mvnw.cmd clean package -DskipTests

# Ejecutar
mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=docker
```

> **Nota importante:** Si el backend falla con el error `Found non-empty schema(s) "public" but no schema history table`, verifica que en `src/main/resources/application-docker.properties` exista la línea:
> ```properties
> spring.flyway.enabled=false
> ```

---

## Paso 3 — Levantar el Frontend (Next.js)

```bash
cd citytransit-web

# Instalar dependencias (solo la primera vez)
npm install

# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en **http://localhost:3000**

> **Nota importante:** Si el frontend falla con errores de compilación relacionados con conflictos de merge (`<<<<<<< HEAD`), ejecuta este script de PowerShell para resolverlos todos automáticamente:
>
> ```powershell
> # Desde la carpeta citytransit-web
> powershell -ExecutionPolicy Bypass -Command "
> Get-ChildItem -Recurse -Include *.tsx,*.ts,*.css,*.js,*.json | foreach {
>   \$lines=[System.IO.File]::ReadAllLines(\$_.FullName,[System.Text.Encoding]::UTF8)
>   \$result=[System.Collections.Generic.List[string]]::new()
>   \$skip=\$false
>   foreach(\$l in \$lines){
>     if(\$l -match '^<<<<<<< '){\$skip=\$false;continue}
>     elseif(\$l -eq '======='){\$skip=\$true;continue}
>     elseif(\$l -match '^>>>>>>> '){\$skip=\$false;continue}
>     elseif(-not \$skip){\$result.Add(\$l)}
>   }
>   [System.IO.File]::WriteAllLines(\$_.FullName,\$result,[System.Text.UTF8Encoding]::new(\$false))
> }
> Write-Host 'Conflictos resueltos'
> "
> ```

---

## Paso 4 (Opcional) — Levantar el Servicio de Analytics (Python)

```bash
cd analytics-service

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servicio
python start_simple.py
```

O con Docker (desde `citytransit-backend`):

```bash
docker-compose up -d analytics
```

---

## URLs de Acceso

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8080 |
| Swagger UI | http://localhost:8080/swagger-ui.html |
| GraphiQL | http://localhost:8080/graphiql |
| Actuator Health | http://localhost:8080/actuator/health |
| PgAdmin | http://localhost:5050 |
| Analytics API | http://localhost:8001 |
| ClickHouse HTTP | http://localhost:8123 |

---

## Credenciales

| Servicio | Usuario | Contraseña |
|---|---|---|
| App (login web) | admin@citytransit.com | admin123 |
| PostgreSQL | postgres | redfire007 |
| MongoDB | admin | redfire007 |
| Redis | — | redfire007 |
| ClickHouse | default | redfire007 |

---

## Detener Todo

```bash
cd citytransit-backend
docker-compose down
```

Para detener también el frontend, presiona `Ctrl+C` en la terminal donde corre `npm run dev`.

---

## Solución de Problemas Frecuentes

### El backend no inicia — error de Flyway

**Error:** `Found non-empty schema(s) "public" but no schema history table`

**Solución:** Agrega esta línea en `citytransit-backend/src/main/resources/application-docker.properties`:
```properties
spring.flyway.enabled=false
```
Luego reconstruye: `docker-compose up -d --build backend`

---

### El frontend no compila — errores de merge

**Error:** `Merge conflict marker encountered`

**Solución:** Ver la nota en el Paso 3 para ejecutar el script de resolución automática de conflictos.

---

### Docker no inicia

1. Abre Docker Desktop manualmente y espera a que el ícono en la barra de tareas esté estable.
2. Vuelve a ejecutar el comando de Docker.

---

### Puerto ya en uso

Si el puerto 3000 está ocupado, Next.js usará automáticamente el 3001. Para liberar el puerto 3000:

```bash
# Encontrar el PID
netstat -ano | findstr ":3000 "
# Matar el proceso (reemplaza <PID> con el número encontrado)
taskkill /PID <PID> /F
```
