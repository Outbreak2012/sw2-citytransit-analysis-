"""
Script para poblar MongoDB con datos de feedback realistas
para el análisis de sentimientos en CityTransit
"""
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
import sys
sys.path.insert(0, '.')

# Conectar a MongoDB con autenticación
client = MongoClient('mongodb://admin:admin123@localhost:27017/')
db = client['paytransit']

# Feedback realista de transporte público en Santa Cruz, Bolivia
FEEDBACK_POSITIVE = [
    # Servicio
    "Excelente servicio, el micro llegó puntual y el conductor muy amable",
    "Muy buen viaje, el bus estaba limpio y con aire acondicionado funcionando",
    "Me encanta el nuevo sistema de tarjetas, muy práctico y rápido",
    "Servicio de primera, llegué a tiempo a mi trabajo gracias al transporte",
    "El conductor fue muy profesional y respetó todas las paradas",
    "Chévere el aire acondicionado, hace mucha falta con este calor cruceño",
    "La app funciona perfecto, puedo ver cuando llega el micro",
    "Muy satisfecho con el servicio, lo recomiendo totalmente",
    "Bus nuevo y cómodo, se nota la inversión en transporte",
    "Excelente la frecuencia de los buses, no esperé más de 5 minutos",
    # Específicos de Bolivia
    "Qué lindo el servicio, muy camba el trato del chofer",
    "Todo joya, el micro llegó rapidingo",
    "Súper bien la línea 16, siempre puntual",
    "Gracias al transporte llegué temprano al trabajo en la Doble Vía",
    "Muy bueno el recorrido por el 2do anillo, rápido y seguro",
    "El servicio mejoró bastante, ya no es como antes",
    "Felicitaciones al conductor de la línea 72, muy atento",
    "Me gusta que ahora hay más buses con aire acondicionado",
    "El sistema de pago electrónico es muy conveniente",
    "Excelente que pusieron wifi en algunos buses",
]

FEEDBACK_NEGATIVE = [
    # Quejas generales
    "Pésimo servicio, el bus nunca llegó y perdí mi cita",
    "Muy mal, el conductor fue grosero cuando le pedí mi vuelto",
    "El micro estaba sucio y maloliente, una vergüenza",
    "Llegué tarde al trabajo por culpa del transporte, siempre lo mismo",
    "Demasiado caro el pasaje para el servicio que dan",
    "El aire acondicionado no funcionaba y hacía un calor insoportable",
    "El conductor manejaba como loco, temí por mi vida",
    "Casi me caigo porque arrancó sin que me sentara",
    "Inseguro, había mucha gente parada y nadie controlaba",
    "La tarjeta no me funcionó y el conductor no quiso ayudarme",
    # Específicos de Bolivia
    "Qué mal servicio, el micro me dejó botado en el 3er anillo",
    "Pésimo, el chofer no respetó la parada del mercado Los Pozos",
    "Terrible la demora, esperé más de 40 minutos en la parada",
    "El micro iba repleto y el conductor seguía subiendo gente",
    "Queja formal por maltrato del conductor de la línea 18",
    "Inaceptable que no haya frecuencia en hora pico",
    "El bus olía horrible, creo que no lo limpian nunca",
    "Me cobraron de más y no me dieron cambio correcto",
    "El conductor hablaba por celular mientras manejaba",
    "No respetan a los adultos mayores, nadie les cede el asiento",
]

FEEDBACK_NEUTRAL = [
    "El servicio estuvo normal, nada especial que reportar",
    "Llegó más o menos a tiempo, dentro de lo esperado",
    "El viaje fue regular, sin problemas ni destacables",
    "No tengo quejas pero tampoco elogios",
    "Funcionó como siempre, ni bien ni mal",
    "El bus pasó, cumplió su función básica",
    "Normal el servicio de hoy, como cualquier otro día",
    "Sin comentarios particulares sobre el viaje",
    "Como cualquier otro día de transporte público",
    "Ni bueno ni malo, simplemente funcional",
    "El micro llegó, eso es lo importante",
    "Viaje estándar, sin novedades",
    "Todo dentro de lo normal",
    "Servicio básico pero cumple",
    "Sin sorpresas, el servicio habitual",
]

# Rutas de Santa Cruz
RUTAS = [
    {"id": 1, "nombre": "Línea 1 - Villa 1ro de Mayo"},
    {"id": 2, "nombre": "Línea 2 - Plan 3000"},
    {"id": 3, "nombre": "Línea 5 - La Guardia"},
    {"id": 4, "nombre": "Línea 8 - Radial 17-1/2"},
    {"id": 5, "nombre": "Línea 10 - Equipetrol"},
    {"id": 6, "nombre": "Línea 12 - Los Lotes"},
    {"id": 7, "nombre": "Línea 16 - Pampa de la Isla"},
    {"id": 8, "nombre": "Línea 18 - Montero"},
    {"id": 9, "nombre": "Línea 21 - Satélite Norte"},
    {"id": 10, "nombre": "Línea 72 - Circunvalación"},
]

# Categorías de feedback
CATEGORIAS = [
    "servicio_general",
    "puntualidad",
    "limpieza",
    "trato_personal",
    "seguridad",
    "comodidad",
    "precio",
    "frecuencia",
    "app_tecnologia",
    "accesibilidad"
]

# Palabras clave por categoría
KEYWORDS = {
    "servicio_general": ["servicio", "transporte", "bus", "micro"],
    "puntualidad": ["puntual", "tarde", "demora", "tiempo", "espera"],
    "limpieza": ["limpio", "sucio", "limpieza", "olor", "basura"],
    "trato_personal": ["conductor", "chofer", "amable", "grosero", "atención"],
    "seguridad": ["seguro", "inseguro", "peligro", "robo", "accidente"],
    "comodidad": ["cómodo", "asiento", "aire", "espacio", "lleno"],
    "precio": ["caro", "precio", "pasaje", "pago", "tarjeta"],
    "frecuencia": ["frecuencia", "espera", "minutos", "hora"],
    "app_tecnologia": ["app", "aplicación", "tarjeta", "sistema", "wifi"],
    "accesibilidad": ["acceso", "rampa", "discapacidad", "mayor"]
}

def detect_category(text):
    """Detectar categoría basada en palabras clave"""
    text_lower = text.lower()
    for category, keywords in KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return "servicio_general"

def generate_feedback_documents(count=500):
    """Generar documentos de feedback"""
    documents = []
    
    # Distribución: 40% positivo, 30% negativo, 30% neutral
    positive_count = int(count * 0.4)
    negative_count = int(count * 0.3)
    neutral_count = count - positive_count - negative_count
    
    feedbacks = []
    feedbacks.extend([(f, "POSITIVE") for f in random.choices(FEEDBACK_POSITIVE, k=positive_count)])
    feedbacks.extend([(f, "NEGATIVE") for f in random.choices(FEEDBACK_NEGATIVE, k=negative_count)])
    feedbacks.extend([(f, "NEUTRAL") for f in random.choices(FEEDBACK_NEUTRAL, k=neutral_count)])
    
    random.shuffle(feedbacks)
    
    for i, (comentario, sentimiento) in enumerate(feedbacks):
        # Fecha aleatoria en los últimos 30 días
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        created_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        # Seleccionar ruta aleatoria
        ruta = random.choice(RUTAS)
        
        # Detectar categoría
        categoria = detect_category(comentario)
        
        # Calcular prioridad basada en sentimiento
        if sentimiento == "NEGATIVE":
            prioridad = random.randint(3, 5)
        elif sentimiento == "POSITIVE":
            prioridad = random.randint(1, 2)
        else:
            prioridad = random.randint(2, 3)
        
        # Score de confianza
        confidence = round(random.uniform(0.75, 0.98), 2)
        
        doc = {
            "comentario": comentario,
            "sentimiento": sentimiento,
            "confidence_score": confidence,
            "ruta_id": ruta["id"],
            "ruta_nombre": ruta["nombre"],
            "categoria": categoria,
            "prioridad": prioridad,
            "usuario_id": random.randint(1000, 9999),
            "created_at": created_at,
            "processed": True,
            "source": "app_mobile",
            "metadata": {
                "device": random.choice(["android", "ios", "web"]),
                "app_version": random.choice(["2.1.0", "2.2.0", "2.3.0"]),
                "location": {
                    "lat": round(-17.7833 + random.uniform(-0.1, 0.1), 6),
                    "lng": round(-63.1821 + random.uniform(-0.1, 0.1), 6)
                }
            }
        }
        
        documents.append(doc)
    
    return documents

def generate_sentiment_analysis_logs(count=200):
    """Generar logs de análisis para métricas"""
    logs = []
    
    for i in range(count):
        days_ago = random.randint(0, 30)
        
        log = {
            "timestamp": datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23)),
            "texts_analyzed": random.randint(1, 50),
            "avg_confidence": round(random.uniform(0.7, 0.95), 2),
            "positive_count": random.randint(5, 30),
            "negative_count": random.randint(2, 15),
            "neutral_count": random.randint(10, 40),
            "processing_time_ms": random.randint(50, 500),
            "model_used": "nlptown/bert-base-multilingual-uncased-sentiment"
        }
        
        logs.append(log)
    
    return logs

def main():
    print("🚀 Poblando MongoDB con datos de feedback para análisis de sentimientos...")
    print(f"📊 Base de datos: {db.name}")
    
    # Limpiar colecciones existentes
    print("\n🧹 Limpiando colecciones existentes...")
    db.user_feedback.delete_many({})
    db.sentiment_analysis_logs.delete_many({})
    
    # Generar e insertar feedback
    print("\n📝 Generando feedback de usuarios...")
    feedbacks = generate_feedback_documents(500)
    result = db.user_feedback.insert_many(feedbacks)
    print(f"✅ Insertados {len(result.inserted_ids)} documentos de feedback")
    
    # Generar e insertar logs de análisis
    print("\n📊 Generando logs de análisis...")
    logs = generate_sentiment_analysis_logs(200)
    result = db.sentiment_analysis_logs.insert_many(logs)
    print(f"✅ Insertados {len(result.inserted_ids)} logs de análisis")
    
    # Crear índices
    print("\n🔧 Creando índices...")
    db.user_feedback.create_index("created_at")
    db.user_feedback.create_index("sentimiento")
    db.user_feedback.create_index("ruta_id")
    db.user_feedback.create_index("categoria")
    db.sentiment_analysis_logs.create_index("timestamp")
    print("✅ Índices creados")
    
    # Mostrar resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE DATOS GENERADOS")
    print("="*50)
    
    # Conteo por sentimiento
    print("\n🎭 Distribución de sentimientos:")
    for sentiment in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
        count = db.user_feedback.count_documents({"sentimiento": sentiment})
        pct = (count / 500) * 100
        emoji = "😊" if sentiment == "POSITIVE" else "😡" if sentiment == "NEGATIVE" else "😐"
        print(f"   {emoji} {sentiment}: {count} ({pct:.1f}%)")
    
    # Conteo por categoría
    print("\n📁 Distribución por categoría:")
    for categoria in CATEGORIAS:
        count = db.user_feedback.count_documents({"categoria": categoria})
        if count > 0:
            print(f"   - {categoria}: {count}")
    
    # Conteo por ruta
    print("\n🚌 Top 5 rutas con más feedback:")
    pipeline = [
        {"$group": {"_id": "$ruta_nombre", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    for ruta in db.user_feedback.aggregate(pipeline):
        print(f"   - {ruta['_id']}: {ruta['count']}")
    
    print("\n✅ ¡Población de datos completada!")
    print("🔄 Reinicia el servicio de analytics o actualiza el dashboard para ver los nuevos datos.")

if __name__ == "__main__":
    main()
