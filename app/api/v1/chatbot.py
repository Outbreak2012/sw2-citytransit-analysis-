"""
Chatbot API para CityTransit/PayTransit
========================================
Proporciona respuestas sobre la empresa y el uso del ML.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import re
from datetime import datetime

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatMessage(BaseModel):
    """Mensaje del chat"""
    role: str  # 'user' o 'assistant'
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Solicitud de chat"""
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    """Respuesta del chat"""
    message: str
    suggestions: List[str] = []
    related_topics: List[str] = []
    timestamp: str


# Base de conocimiento sobre la empresa y ML
KNOWLEDGE_BASE = {
    "empresa": {
        "keywords": ["empresa", "citytransit", "paytransit", "compañía", "quienes somos", "qué hacen", "sobre nosotros", "about"],
        "response": """🚌 **Bienvenido a PayTransit/CityTransit**

Somos un sistema de pago inteligente para transporte público que combina tecnología de vanguardia con Machine Learning para mejorar la experiencia de usuarios y operadores.

**Nuestra misión:**
Transformar el transporte público mediante pagos sin fricción y análisis predictivo.

**¿Qué ofrecemos?**
• 💳 Pagos con tarjeta NFC inteligente
• 📊 Análisis de datos en tiempo real
• 🤖 Predicciones de demanda con IA
• 😊 Análisis de sentimientos de usuarios
• 📈 Dashboards para operadores

¿Te gustaría saber más sobre alguna funcionalidad específica?""",
        "suggestions": ["¿Cómo funciona el ML?", "¿Qué modelos usan?", "¿Cómo predecir demanda?"]
    },
    
    "ml_general": {
        "keywords": ["ml", "machine learning", "inteligencia artificial", "ia", "modelos", "predicciones", "como funciona"],
        "response": """🤖 **Machine Learning en PayTransit**

Utilizamos 3 modelos principales de ML/DL para mejorar el servicio:

**1. LSTM (Deep Learning)** 📈
Predicción de demanda de pasajeros usando series temporales.

**2. BERT (NLP)** 💬
Análisis de sentimientos de comentarios y feedback.

**3. DBSCAN (Clustering)** 👥
Segmentación de usuarios para personalización.

Cada modelo está optimizado para trabajar en tiempo real y proporcionar insights accionables.

¿Sobre cuál modelo te gustaría saber más?""",
        "suggestions": ["Cuéntame sobre LSTM", "¿Cómo funciona BERT?", "Explicar DBSCAN"]
    },
    
    "lstm": {
        "keywords": ["lstm", "prediccion demanda", "series temporales", "demanda", "pasajeros", "pronostico", "forecast"],
        "response": """📈 **Modelo LSTM - Predicción de Demanda**

**¿Qué es LSTM?**
Long Short-Term Memory es una red neuronal recurrente diseñada para aprender patrones en series temporales.

**¿Cómo lo usamos?**
• Predecimos la demanda de pasajeros por hora y ruta
• Analizamos 24 horas de histórico para cada predicción
• Consideramos factores como clima, día de la semana, feriados

**Características del modelo:**
```
Arquitectura:
├── LSTM 128 unidades
├── Dropout 0.2
├── LSTM 64 unidades
├── Dropout 0.2
├── LSTM 32 unidades
└── Dense (salida)
```

**¿Cómo usar la API?**
```
POST /api/v1/analytics/demand/predict
GET  /api/v1/analytics/demand/forecast/{route_id}
```

**Ejemplo de respuesta:**
- Pasajeros predichos: 150
- Confianza: 87%
- Tendencia: Creciente""",
        "suggestions": ["¿Cómo usar la predicción?", "¿Qué datos necesita?", "Ver ejemplo de código"]
    },
    
    "bert": {
        "keywords": ["bert", "sentimientos", "sentiment", "nlp", "comentarios", "feedback", "opiniones", "analisis texto"],
        "response": """💬 **Modelo BERT - Análisis de Sentimientos**

**¿Qué es BERT?**
Bidirectional Encoder Representations from Transformers es un modelo de NLP de última generación.

**¿Cómo lo usamos?**
• Analizamos comentarios y feedback de usuarios
• Detectamos sentimientos: Positivo, Neutral, Negativo
• Identificamos palabras clave y emociones principales

**Modelos soportados:**
1. `nlptown/bert-base-multilingual-uncased-sentiment` (Multilingüe ⭐)
2. `cardiffnlp/twitter-xlm-roberta-base-sentiment` (XLM-RoBERTa)
3. `distilbert-base-uncased-finetuned-sst-2-english` (Fallback)

**¿Cómo usar la API?**
```
POST /api/v1/analytics/sentiment/analyze
Body: { "text": "El servicio fue excelente" }
```

**Ejemplo de respuesta:**
- Sentimiento: Positivo
- Confianza: 92%
- Emoción: Satisfacción""",
        "suggestions": ["¿Cómo analizar un comentario?", "¿Qué idiomas soporta?", "Ver tendencias de sentimiento"]
    },
    
    "dbscan": {
        "keywords": ["dbscan", "cluster", "segmentacion", "usuarios", "grupos", "perfiles", "clustering"],
        "response": """👥 **Modelo DBSCAN - Segmentación de Usuarios**

**¿Qué es DBSCAN?**
Density-Based Spatial Clustering es un algoritmo que agrupa usuarios según sus patrones de comportamiento.

**¿Cómo lo usamos?**
• Identificamos grupos de usuarios con comportamiento similar
• Detectamos usuarios atípicos (outliers)
• Personalizamos recomendaciones

**Perfiles típicos identificados:**
🎯 **Commuter Regular** - Viaja en horas pico, misma ruta
👴 **Usuario Ocasional** - Viajes esporádicos
🎒 **Estudiante** - Horarios académicos
💼 **Ejecutivo** - Rutas premium, alto gasto

**¿Cómo usar la API?**
```
GET  /api/v1/analytics/users/clusters
POST /api/v1/analytics/users/segment
```

**Métricas por cluster:**
- Frecuencia promedio de viajes
- Gasto promedio
- Rutas preferidas
- Horarios de uso""",
        "suggestions": ["¿Cómo obtener mi perfil?", "¿Qué son los outliers?", "Personalizar recomendaciones"]
    },
    
    "api": {
        "keywords": ["api", "endpoint", "endpoints", "integrar", "documentacion", "swagger", "rest"],
        "response": """🔌 **API de Analytics - Endpoints Disponibles**

**Base URL:** `http://localhost:8000`

**📊 Predicción de Demanda (LSTM)**
```
POST /api/v1/analytics/demand/predict
GET  /api/v1/analytics/demand/forecast/{route_id}
GET  /api/v1/analytics/demand/trends
```

**💬 Análisis de Sentimientos (BERT)**
```
POST /api/v1/analytics/sentiment/analyze
GET  /api/v1/analytics/sentiment/summary
GET  /api/v1/analytics/sentiment/trends
```

**👥 Segmentación de Usuarios (DBSCAN)**
```
GET  /api/v1/analytics/users/clusters
POST /api/v1/analytics/users/segment
GET  /api/v1/analytics/users/outliers
```

**📈 Reportes y KPIs**
```
GET  /api/v1/reports/kpis
GET  /api/v1/reports/dashboard
```

**📚 Documentación interactiva:**
- Swagger UI: `/docs`
- ReDoc: `/redoc`""",
        "suggestions": ["¿Cómo autenticarme?", "Ver ejemplo de predicción", "Obtener KPIs"]
    },
    
    "uso_prediccion": {
        "keywords": ["usar prediccion", "como predecir", "ejemplo prediccion", "probar modelo", "tutorial"],
        "response": """📖 **Tutorial: Usar Predicción de Demanda**

**Paso 1: Obtener token de autenticación**
```javascript
const token = await authService.login(email, password);
```

**Paso 2: Hacer predicción rápida**
```javascript
const response = await fetch('/api/ml/predict-demand/quick?rutaId=1', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const prediction = await response.json();
```

**Paso 3: Interpretar resultados**
```json
{
  "rutaId": 1,
  "pasajerosPredichos": 145,
  "confianza": 0.87,
  "ocupacionPredicha": 72.5,
  "nivelDemanda": "ALTO",
  "recomendacion": "Añadir unidad adicional"
}
```

**Desde el Dashboard:**
1. Ir a Analytics → Predicción
2. Seleccionar ruta y fecha
3. Ver gráfico de predicción

¿Necesitas ayuda con algo más específico?""",
        "suggestions": ["Ver código completo", "Predicción por horas", "Entender la confianza"]
    },
    
    "kpis": {
        "keywords": ["kpi", "kpis", "metricas", "indicadores", "dashboard", "tiempo real"],
        "response": """📊 **KPIs en Tiempo Real**

PayTransit proporciona métricas clave actualizadas en tiempo real:

**Métricas principales:**
• 👥 **Pasajeros activos** - Usuarios usando el sistema ahora
• 🚌 **Vehículos activos** - Flota en operación
• 📈 **Ocupación promedio** - % de capacidad utilizada
• 🔮 **Demanda predicha** - Proyección próximas horas
• 😊 **Score de sentimiento** - Satisfacción general

**Acceso a KPIs:**
```
GET /api/v1/reports/kpis
```

**Ejemplo de respuesta:**
```json
{
  "active_passengers": 1250,
  "active_vehicles": 45,
  "avg_occupancy": 68.5,
  "predicted_demand": 1450,
  "sentiment_score": 4.2
}
```

Los KPIs se actualizan cada 30 segundos y alimentan los dashboards del sistema.""",
        "suggestions": ["¿Cómo ver el dashboard?", "Alertas automáticas", "Exportar reportes"]
    },
    
    "ayuda": {
        "keywords": ["ayuda", "help", "comandos", "que puedes hacer", "opciones", "menu"],
        "response": """🆘 **Centro de Ayuda - PayTransit Bot**

Puedo ayudarte con los siguientes temas:

**🏢 Sobre la empresa**
• ¿Qué es PayTransit?
• ¿Cuáles son sus servicios?

**🤖 Machine Learning**
• ¿Qué modelos usan?
• ¿Cómo funciona LSTM?
• ¿Qué hace BERT?
• Explicar DBSCAN

**🔌 API y Desarrollo**
• ¿Qué endpoints hay?
• ¿Cómo usar la API?
• Ver documentación

**📊 Analytics**
• ¿Qué KPIs miden?
• ¿Cómo predecir demanda?
• Análisis de sentimientos

**Escribe tu pregunta o selecciona una sugerencia!**""",
        "suggestions": ["¿Qué es PayTransit?", "¿Cómo funciona el ML?", "Ver API endpoints"]
    },
    
    "saludo": {
        "keywords": ["hola", "hi", "hello", "buenos dias", "buenas tardes", "buenas noches", "hey"],
        "response": """👋 **¡Hola! Bienvenido al asistente de PayTransit**

Soy tu guía virtual para aprender sobre nuestra plataforma de transporte inteligente y los modelos de Machine Learning que utilizamos.

**¿En qué puedo ayudarte hoy?**

Puedo explicarte sobre:
• 🏢 La empresa y sus servicios
• 🤖 Los modelos de ML (LSTM, BERT, DBSCAN)
• 🔌 Cómo usar la API
• 📊 Métricas y KPIs

¡Solo pregúntame lo que necesites saber!""",
        "suggestions": ["¿Qué es PayTransit?", "¿Qué modelos de ML usan?", "¿Cómo predecir demanda?"]
    }
}

# Respuesta por defecto
DEFAULT_RESPONSE = {
    "response": """🤔 **No estoy seguro de entender tu pregunta**

Pero puedo ayudarte con estos temas:

• **Sobre la empresa**: "¿Qué es PayTransit?"
• **Machine Learning**: "¿Cómo funciona el ML?"
• **Modelos específicos**: "Explícame LSTM", "¿Qué hace BERT?"
• **API**: "¿Qué endpoints tienen?"
• **Métricas**: "¿Qué KPIs miden?"

¿Podrías reformular tu pregunta o elegir uno de estos temas?""",
    "suggestions": ["¿Qué es PayTransit?", "¿Cómo funciona el ML?", "Necesito ayuda"]
}


def find_best_match(message: str) -> dict:
    """
    Encuentra la mejor respuesta basada en el mensaje del usuario.
    Usa matching de keywords con scoring.
    """
    message_lower = message.lower().strip()
    
    # Normalizar texto (remover acentos comunes)
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', '¿': '', '?': '', '!': '', '¡': ''
    }
    for old, new in replacements.items():
        message_lower = message_lower.replace(old, new)
    
    best_match = None
    best_score = 0
    
    for topic, data in KNOWLEDGE_BASE.items():
        score = 0
        for keyword in data["keywords"]:
            if keyword in message_lower:
                # Dar más peso a keywords más largos
                score += len(keyword)
        
        if score > best_score:
            best_score = score
            best_match = data
    
    if best_match and best_score > 0:
        return best_match
    
    return DEFAULT_RESPONSE


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal del chatbot.
    Procesa el mensaje del usuario y devuelve una respuesta contextual.
    Usa LLM si está disponible, sino fallback a reglas.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
    
    # Intentar usar el servicio de IA con LangChain
    try:
        from app.services.ai_service import ai_service
        
        result = await ai_service.chat(request.message)
        
        return ChatResponse(
            message=result["message"],
            suggestions=_get_contextual_suggestions(request.message),
            related_topics=list(KNOWLEDGE_BASE.keys())[:5],
            timestamp=result.get("timestamp", datetime.now().isoformat())
        )
    except Exception as e:
        # Fallback a sistema de reglas
        import logging
        logging.warning(f"AI Service no disponible, usando fallback: {e}")
    
    # Fallback: Buscar mejor respuesta con keywords
    match = find_best_match(request.message)
    
    return ChatResponse(
        message=match["response"],
        suggestions=match.get("suggestions", []),
        related_topics=list(KNOWLEDGE_BASE.keys())[:5],
        timestamp=datetime.now().isoformat()
    )


def _get_contextual_suggestions(message: str) -> List[str]:
    """Generar sugerencias basadas en el contexto del mensaje."""
    message_lower = message.lower()
    
    if any(w in message_lower for w in ['kpi', 'metricas', 'estadisticas']):
        return ["Ver predicción de demanda", "Analizar sentimientos", "Segmentación de usuarios"]
    
    if any(w in message_lower for w in ['demanda', 'lstm', 'prediccion']):
        return ["Ver KPIs actuales", "¿Cómo funciona LSTM?", "Predicción para ruta 2"]
    
    if any(w in message_lower for w in ['sentimiento', 'bert', 'feedback']):
        return ["Ver resumen de sentimientos", "Analizar un texto", "¿Qué es BERT?"]
    
    if any(w in message_lower for w in ['usuario', 'segmento', 'cluster']):
        return ["Ver clusters actuales", "¿Qué es DBSCAN?", "Outliers detectados"]
    
    return ["Ver KPIs", "Predecir demanda", "Analizar sentimiento", "Ver rutas"]


@router.post("/chat/ai")
async def chat_with_ai(request: ChatRequest):
    """
    Endpoint de chat que usa exclusivamente el servicio de IA con LangChain.
    Proporciona respuestas más inteligentes usando GPT-4.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
    
    try:
        from app.services.ai_service import ai_service
        
        result = await ai_service.chat(request.message)
        
        return {
            "message": result["message"],
            "mode": result.get("mode", "unknown"),
            "model": result.get("model", "unknown"),
            "tokens_used": result.get("tokens_used", 0),
            "cost": result.get("cost", 0),
            "response_time": result.get("response_time", 0),
            "suggestions": _get_contextual_suggestions(request.message),
            "timestamp": result.get("timestamp", datetime.now().isoformat())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en servicio de IA: {str(e)}")


@router.post("/nl2sql")
async def natural_language_to_sql(request: ChatRequest):
    """
    Convertir pregunta en lenguaje natural a SQL.
    Ejecuta la consulta y devuelve los resultados.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
    
    try:
        from app.services.nl2sql_service import nl2sql_service
        
        result = await nl2sql_service.execute(request.message)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en NL2SQL: {str(e)}")


@router.post("/nl2sql/convert")
async def convert_to_sql(request: ChatRequest):
    """
    Solo convertir pregunta a SQL sin ejecutar.
    Útil para validar o modificar la consulta antes de ejecutar.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
    
    try:
        from app.services.nl2sql_service import nl2sql_service
        
        result = await nl2sql_service.convert(request.message)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en conversión: {str(e)}")


@router.get("/status")
async def get_ai_status():
    """
    Obtener estado de los servicios de IA.
    """
    status = {
        "chatbot": "active",
        "mode": "fallback",
        "services": {}
    }
    
    try:
        from app.services.ai_service import ai_service, HAS_LANGCHAIN, HAS_OPENAI
        from app.core.config import settings
        
        status["services"]["langchain"] = "available" if HAS_LANGCHAIN else "not_installed"
        status["services"]["openai"] = "available" if HAS_OPENAI else "not_installed"
        status["services"]["api_key_configured"] = bool(settings.OPENAI_API_KEY)
        
        if ai_service.is_initialized:
            status["mode"] = "fallback" if ai_service.fallback_mode else "llm"
            status["model"] = settings.OPENAI_MODEL if not ai_service.fallback_mode else "rule-based"
    except:
        pass
    
    try:
        from app.services.nl2sql_service import nl2sql_service, HAS_LANGCHAIN as NL2SQL_HAS_LC
        status["services"]["nl2sql"] = "available" if nl2sql_service.is_initialized else "not_initialized"
    except:
        status["services"]["nl2sql"] = "not_available"
    
    return status


@router.get("/suggestions")
async def get_suggestions():
    """
    Obtener sugerencias iniciales para el chatbot.
    """
    return {
        "greeting": "👋 ¡Hola! Soy el asistente de PayTransit. ¿En qué puedo ayudarte?",
        "suggestions": [
            "¿Qué es PayTransit?",
            "¿Cómo funciona el Machine Learning?",
            "Explícame el modelo LSTM",
            "¿Cómo analizar sentimientos?",
            "Ver API endpoints"
        ],
        "ai_suggestions": [
            "Muéstrame los KPIs actuales",
            "¿Cuántos pasajeros hubo hoy?",
            "Predice la demanda para la ruta 1",
            "Analiza: 'El servicio es excelente'",
            "¿Cómo están segmentados los usuarios?"
        ],
        "categories": [
            {"id": "empresa", "name": "Sobre la Empresa", "icon": "🏢"},
            {"id": "ml", "name": "Machine Learning", "icon": "🤖"},
            {"id": "api", "name": "API & Desarrollo", "icon": "🔌"},
            {"id": "analytics", "name": "Analytics", "icon": "📊"},
            {"id": "nl2sql", "name": "Consultas SQL", "icon": "🔍"}
        ]
    }


@router.get("/topics")
async def get_topics():
    """
    Obtener lista de temas disponibles.
    """
    topics = []
    for topic_id, data in KNOWLEDGE_BASE.items():
        topics.append({
            "id": topic_id,
            "keywords": data["keywords"][:3],
            "preview": data["response"][:100] + "..."
        })
    return {"topics": topics}
