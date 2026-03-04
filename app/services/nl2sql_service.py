"""
NL2SQL - Natural Language to SQL
=================================
Convierte preguntas en lenguaje natural a consultas SQL.
Soporta ClickHouse y PostgreSQL.

Utiliza LLM Service multi-proveedor:
- Ollama (local, gratis)
- Groq (API gratis)
- HuggingFace (modelos open-source)
- OpenAI (si hay API key)
"""
import logging
import re
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# Importar LLM Service multi-proveedor
try:
    from app.services.llm_service import llm_service, LLMProvider
    HAS_LLM_SERVICE = True
except ImportError:
    llm_service = None
    HAS_LLM_SERVICE = False
    logger.warning("LLM Service no disponible para NL2SQL")

# Fallback: Intentar importar LangChain directamente
HAS_LANGCHAIN = False
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    HAS_LANGCHAIN = True
except ImportError:
    pass


# Schema de las tablas para contexto del LLM
CLICKHOUSE_SCHEMA = """
-- ClickHouse Schema (OLAP Analytics)

CREATE TABLE pasajes (
    id UInt64,
    usuario_id UInt64,
    tarjeta_id UInt64,
    vehiculo_id UInt64,
    ruta_id UInt64,
    monto Decimal(10,2),
    fecha DateTime,
    hora_pico Bool,
    ocupacion Float32,
    tipo_pago String -- 'NFC', 'QR', 'EFECTIVO'
);

CREATE TABLE rutas (
    id UInt64,
    nombre String,
    origen String,
    destino String,
    distancia_km Float32,
    tiempo_estimado_min UInt16,
    tarifa Decimal(10,2)
);

CREATE TABLE usuarios (
    id UInt64,
    nombre String,
    email String,
    fecha_registro DateTime,
    saldo Decimal(10,2),
    tipo_usuario String -- 'REGULAR', 'ESTUDIANTE', 'PREMIUM'
);

CREATE TABLE vehiculos (
    id UInt64,
    placa String,
    ruta_id UInt64,
    capacidad UInt16,
    estado String -- 'ACTIVO', 'MANTENIMIENTO', 'INACTIVO'
);
"""

# Patrones para conversion sin LLM
SQL_PATTERNS = [
    # Transacciones
    (r'(transacciones?|pasajes?|viajes?)\s*(de\s+)?hoy', 
     "SELECT * FROM pasajes WHERE toDate(fecha) = today() ORDER BY fecha DESC LIMIT 100"),
    
    (r'(transacciones?|pasajes?|viajes?)\s*(de\s+)?ayer',
     "SELECT * FROM pasajes WHERE toDate(fecha) = today() - 1 ORDER BY fecha DESC LIMIT 100"),
    
    (r'(ultim[ao]s?\s+)?(\d+)\s*(transacciones?|pasajes?|viajes?)',
     "SELECT * FROM pasajes ORDER BY fecha DESC LIMIT {2}"),
    
    # Conteos
    (r'cuant[ao]s?\s*(usuarios?|pasajeros?|clientes?)',
     "SELECT count(DISTINCT usuario_id) as total_usuarios FROM pasajes WHERE toDate(fecha) >= today() - 30"),
    
    (r'cuant[ao]s?\s*(vehiculos?|buses?|unidades?)',
     "SELECT count(*) as total_vehiculos, estado FROM vehiculos GROUP BY estado"),
    
    (r'cuant[ao]s?\s*(transacciones?|pasajes?|viajes?)',
     "SELECT count(*) as total FROM pasajes WHERE toDate(fecha) = today()"),
    
    # Ingresos/Revenue
    (r'(ingresos?|revenue|ventas?|recaudacion)\s*(de\s+)?hoy',
     "SELECT sum(monto) as ingresos_hoy FROM pasajes WHERE toDate(fecha) = today()"),
    
    (r'(ingresos?|revenue|ventas?)\s*(de\s+)?(este\s+)?mes',
     "SELECT sum(monto) as ingresos_mes FROM pasajes WHERE toStartOfMonth(fecha) = toStartOfMonth(today())"),
    
    # Rutas
    (r'(rutas?|lineas?)\s*(disponibles?|activas?)?',
     "SELECT id, nombre, origen, destino, tarifa FROM rutas ORDER BY id"),
    
    (r'ruta\s*(\d+)',
     "SELECT * FROM rutas WHERE id = {1}"),
    
    # Ocupacion
    (r'ocupacion\s*(promedio|media)?',
     "SELECT avg(ocupacion) as ocupacion_promedio FROM pasajes WHERE toDate(fecha) = today()"),
    
    # Top/Rankings
    (r'(top|mejores?)\s*(\d+)?\s*(rutas?|lineas?)',
     "SELECT ruta_id, count(*) as viajes FROM pasajes WHERE toDate(fecha) >= today() - 7 GROUP BY ruta_id ORDER BY viajes DESC LIMIT {2}"),
    
    (r'(usuarios?|pasajeros?)\s*(mas\s+)?frecuentes?',
     "SELECT usuario_id, count(*) as viajes FROM pasajes GROUP BY usuario_id ORDER BY viajes DESC LIMIT 10"),
    
    # Hora pico
    (r'hora\s*pico',
     "SELECT toHour(fecha) as hora, count(*) as viajes FROM pasajes WHERE toDate(fecha) = today() GROUP BY hora ORDER BY viajes DESC LIMIT 5"),
]


class NL2SQLService:
    """
    Servicio para convertir lenguaje natural a SQL.
    Usa LLM Service multi-proveedor (Ollama, Groq, HuggingFace, OpenAI).
    """
    
    def __init__(self):
        self.llm = None
        self._use_llm_service = HAS_LLM_SERVICE and llm_service and llm_service.is_available
        self._initialize()
    
    @property
    def is_available(self) -> bool:
        """Indica si el servicio esta disponible."""
        return True  # Siempre disponible con regex fallback
    
    @property
    def has_llm(self) -> bool:
        """Indica si tiene LLM configurado."""
        return self._use_llm_service or self.llm is not None
    
    def get_llm_status(self) -> Dict[str, Any]:
        """Obtener estado del LLM."""
        if self._use_llm_service and llm_service:
            return llm_service.get_status()
        elif self.llm:
            return {"active_provider": "openai_legacy", "available": True}
        else:
            return {"active_provider": None, "available": False, "method": "regex_only"}
    
    def _initialize(self):
        """Inicializar LLM si esta disponible."""
        # Prioridad 1: Usar LLM Service multi-proveedor
        if self._use_llm_service:
            logger.info(f"NL2SQL: Usando LLM Service multi-proveedor")
            return
        
        # Prioridad 2: Fallback a LangChain/OpenAI directo
        if not HAS_LANGCHAIN:
            logger.info("NL2SQL: Solo regex disponible (sin LLM)")
            return
        
        if not settings.OPENAI_API_KEY:
            logger.info("NL2SQL: Solo regex disponible (sin API key)")
            return
        
        try:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0,  # Deterministic para SQL
                api_key=settings.OPENAI_API_KEY,
            )
            logger.info("NL2SQL inicializado con LLM")
        except Exception as e:
            logger.error(f"Error inicializando NL2SQL LLM: {e}")
    
    def convert_to_sql(self, query: str, database: str = "clickhouse") -> Dict[str, Any]:
        """
        Convertir pregunta en lenguaje natural a SQL.
        
        Args:
            query: Pregunta en lenguaje natural
            database: Base de datos objetivo ('clickhouse' o 'postgres')
            
        Returns:
            Dict con SQL generado y metadata
        """
        query_lower = query.lower().strip()
        
        # Primero intentar con patrones regex
        sql, pattern_used = self._match_pattern(query_lower)
        if sql:
            return {
                "original_query": query,
                "sql": sql,
                "database": database,
                "method": "pattern_matching",
                "pattern": pattern_used,
                "confidence": 0.9,
                "timestamp": datetime.now().isoformat()
            }
        
        # Si hay LLM Service multi-proveedor, usarlo
        if self._use_llm_service and llm_service:
            try:
                sql = self._generate_with_llm_service(query, database)
                if sql and not sql.startswith("--"):
                    provider_status = llm_service.get_status()
                    return {
                        "original_query": query,
                        "sql": sql,
                        "database": database,
                        "method": "llm_service",
                        "provider": provider_status.get("active_provider", "unknown"),
                        "confidence": 0.85,
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error LLM Service NL2SQL: {e}")
        
        # Fallback: LangChain/OpenAI directo (legacy)
        if self.llm:
            try:
                sql = self._generate_with_llm(query, database)
                return {
                    "original_query": query,
                    "sql": sql,
                    "database": database,
                    "method": "llm_legacy",
                    "model": settings.OPENAI_MODEL,
                    "confidence": 0.85,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error LLM NL2SQL: {e}")
        
        # Fallback: SQL generico
        return {
            "original_query": query,
            "sql": f"-- No se pudo generar SQL para: {query}\n-- Intenta ser mas especifico",
            "database": database,
            "method": "fallback",
            "confidence": 0.0,
            "error": "No se encontro patron coincidente",
            "suggestions": self._get_suggestions(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _match_pattern(self, query: str) -> tuple:
        """Buscar patron coincidente."""
        for pattern, sql_template in SQL_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Reemplazar grupos capturados
                sql = sql_template
                for i, group in enumerate(match.groups(), 1):
                    if group:
                        sql = sql.replace(f"{{{i}}}", group)
                # Limpiar placeholders no usados
                sql = re.sub(r'\{[0-9]+\}', '10', sql)
                return sql, pattern
        return None, None
    
    def _generate_with_llm(self, query: str, database: str) -> str:
        """Generar SQL usando LLM legacy (LangChain/OpenAI directo)."""
        system_prompt = f"""Eres un experto en SQL para {database}.
        
Convierte la siguiente pregunta en una consulta SQL valida.

Schema disponible:
{CLICKHOUSE_SCHEMA}

Reglas:
1. Solo genera la consulta SQL, sin explicaciones
2. Usa sintaxis de {'ClickHouse' if database == 'clickhouse' else 'PostgreSQL'}
3. Incluye LIMIT si no se especifica cantidad
4. Para fechas usa funciones de {database}
5. Solo SELECT, nada de INSERT/UPDATE/DELETE
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        response = self.llm.invoke(messages)
        sql = response.content.strip()
        
        # Limpiar markdown si viene envuelto
        sql = re.sub(r'^```sql\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
        
        return sql
    
    def _generate_with_llm_service(self, query: str, database: str) -> str:
        """
        Generar SQL usando LLM Service multi-proveedor.
        Soporta: Ollama (local), Groq, HuggingFace, OpenAI
        """
        system_prompt = f"""Eres un experto en SQL para {database}.
        
Convierte la siguiente pregunta en una consulta SQL valida.

Schema disponible:
{CLICKHOUSE_SCHEMA}

Reglas:
1. Solo genera la consulta SQL, sin explicaciones ni comentarios
2. Usa sintaxis de {'ClickHouse' if database == 'clickhouse' else 'PostgreSQL'}
3. Incluye LIMIT si no se especifica cantidad
4. Para fechas usa funciones de {database}
5. Solo SELECT, nada de INSERT/UPDATE/DELETE
6. Responde SOLO con la consulta SQL, nada más
"""
        
        # Usar asyncio para llamar al servicio async
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(
            llm_service.generate(query, system_prompt, temperature=0, max_tokens=512)
        )
        
        if not response.success:
            logger.warning(f"LLM Service error: {response.error}")
            return ""
        
        sql = response.content.strip()
        
        # Limpiar markdown si viene envuelto
        sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
        sql = sql.strip()
        
        return sql

    def execute_query(self, sql: str, database: str = "clickhouse") -> Dict[str, Any]:
        """
        Ejecutar consulta SQL.
        
        Args:
            sql: Consulta SQL a ejecutar
            database: Base de datos objetivo
            
        Returns:
            Dict con resultados
        """
        # Validar que sea SELECT
        if not sql.strip().upper().startswith('SELECT'):
            return {
                "success": False,
                "error": "Solo se permiten consultas SELECT",
                "sql": sql
            }
        
        try:
            if database == "clickhouse":
                return self._execute_clickhouse(sql)
            elif database == "postgres":
                return self._execute_postgres(sql)
            else:
                return {
                    "success": False,
                    "error": f"Base de datos no soportada: {database}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql
            }
    
    def _execute_clickhouse(self, sql: str) -> Dict[str, Any]:
        """Ejecutar en ClickHouse."""
        try:
            from app.db.clickhouse import clickhouse_conn
            
            result = clickhouse_conn.execute(sql)
            
            return {
                "success": True,
                "database": "clickhouse",
                "sql": sql,
                "rows": len(result) if result else 0,
                "data": result[:100] if result else [],  # Limitar
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "database": "clickhouse",
                "error": str(e),
                "sql": sql
            }
    
    def _execute_postgres(self, sql: str) -> Dict[str, Any]:
        """Ejecutar en PostgreSQL."""
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DATABASE,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD
            )
            
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "database": "postgres",
                "sql": sql,
                "columns": columns,
                "rows": len(result) if result else 0,
                "data": result[:100] if result else [],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "database": "postgres",
                "error": str(e),
                "sql": sql
            }
    
    def _get_suggestions(self) -> List[str]:
        """Sugerencias de consultas."""
        return [
            "Muestrame las transacciones de hoy",
            "Cuantos usuarios hay activos?",
            "Ingresos de este mes",
            "Top 5 rutas mas usadas",
            "Ocupacion promedio",
            "Usuarios mas frecuentes",
            "Cual es la hora pico?"
        ]


# Instancia global
nl2sql_service = NL2SQLService()
