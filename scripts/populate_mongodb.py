"""
Script para poblar MongoDB con feedback de usuarios sintético
Genera comentarios realistas en español con sentimientos variados
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBFeedbackGenerator:
    """Generador de feedback sintético para MongoDB"""
    
    def __init__(self, host='localhost', port=27017):
        # Conectar con credenciales
        connection_string = f"mongodb://admin:admin123@{host}:{port}/?authSource=admin"
        self.client = MongoClient(connection_string)
        self.db = self.client.citytransit
        
    def create_collections(self):
        """Crear colecciones en MongoDB"""
        logger.info("📊 Preparando colecciones en MongoDB...")
        
        # Crear índices
        self.db.user_feedback.create_index([("timestamp", -1)])
        self.db.user_feedback.create_index([("route_id", 1)])
        self.db.user_feedback.create_index([("sentiment", 1)])
        
        logger.info("✅ Colecciones preparadas")
    
    def get_positive_comments(self):
        """Comentarios positivos en español"""
        return [
            "Excelente servicio, muy puntual y limpio. Lo recomiendo!",
            "El conductor fue muy amable y el bus llegó a tiempo.",
            "Genial experiencia, el bus estaba en perfectas condiciones.",
            "Muy buen servicio, rápido y eficiente. Felicitaciones!",
            "Me encanta usar este servicio, siempre es confiable.",
            "Perfecto! El horario se cumple y los buses son cómodos.",
            "Maravilloso servicio de transporte, seguiré usándolo.",
            "Todo excelente, desde el conductor hasta la limpieza del vehículo.",
            "Muy satisfecho con el servicio, puntual y seguro.",
            "Gran servicio! Los conductores son muy profesionales.",
            "El mejor transporte de la ciudad, sin duda.",
            "Impresionante la puntualidad y comodidad del servicio.",
            "Muy contento con la calidad del servicio ofrecido.",
            "Excelente atención y buses muy limpios.",
            "Servicio de primera, lo uso todos los días.",
            "Me siento seguro viajando en estos buses.",
            "Fantástico! Siempre llego a tiempo gracias a este servicio.",
            "Súper recomendado, excelente relación calidad-precio.",
            "Los conductores son muy amables y respetuosos.",
            "Buses modernos y en muy buen estado.",
        ]
    
    def get_neutral_comments(self):
        """Comentarios neutrales en español"""
        return [
            "El servicio es normal, nada extraordinario.",
            "Cumple con lo esperado, sin problemas mayores.",
            "Es un servicio aceptable para el día a día.",
            "No tengo quejas pero tampoco destacaría algo especial.",
            "El bus llegó un poco tarde pero no fue grave.",
            "Servicio estándar, sin sorpresas.",
            "Todo bien, aunque podría mejorar en algunos aspectos.",
            "El viaje fue tranquilo, sin incidentes.",
            "Servicio adecuado, cumple su función.",
            "No está mal, aunque he visto mejores servicios.",
            "Es aceptable, aunque a veces hay retrasos menores.",
            "El bus estaba un poco lleno pero llegamos bien.",
            "Servicio regular, nada fuera de lo común.",
            "Está bien para el precio que se paga.",
            "El conductor hizo su trabajo normalmente.",
            "Sin problemas pero tampoco sobresale.",
            "Es un servicio promedio, ni bueno ni malo.",
            "Llegué a mi destino sin contratiempos.",
            "El bus podría estar más limpio pero está aceptable.",
            "Servicio común, nada destacable.",
        ]
    
    def get_negative_comments(self):
        """Comentarios negativos en español"""
        return [
            "Muy mal servicio, el bus llegó 30 minutos tarde.",
            "Pésima experiencia, el conductor fue grosero.",
            "El bus estaba sucio y en mal estado.",
            "Horrible servicio, nunca llegan a tiempo.",
            "Muy insatisfecho, demasiadas demoras.",
            "El peor servicio de transporte que he usado.",
            "Los buses están siempre llenos, incómodo.",
            "Mala experiencia, no lo recomiendo para nada.",
            "El conductor manejaba muy mal, sentí peligro.",
            "Servicio lento e ineficiente, una pérdida de tiempo.",
            "Nunca más uso este servicio, muy malo.",
            "Los buses están viejos y sucios.",
            "Mala atención por parte del conductor.",
            "Demasiados retrasos, no se puede confiar.",
            "El bus no pasó y tuve que esperar otro.",
            "Muy incómodo, no hay espacio para todos.",
            "Pésimo servicio al cliente, nadie responde quejas.",
            "Los horarios no se cumplen nunca.",
            "Decepcionante, esperaba mucho más.",
            "No vale lo que cuesta, muy mal servicio.",
        ]
    
    def get_comment_by_sentiment(self, sentiment):
        """Obtener comentario según sentimiento"""
        if sentiment == "POSITIVE":
            return random.choice(self.get_positive_comments())
        elif sentiment == "NEGATIVE":
            return random.choice(self.get_negative_comments())
        else:  # NEUTRAL
            return random.choice(self.get_neutral_comments())
    
    def get_rating_by_sentiment(self, sentiment):
        """Obtener rating según sentimiento"""
        if sentiment == "POSITIVE":
            return random.randint(4, 5)
        elif sentiment == "NEGATIVE":
            return random.randint(1, 2)
        else:  # NEUTRAL
            return 3
    
    def generate_feedback(self, num_samples=5000, months=6):
        """Generar feedback sintético"""
        logger.info(f"🔄 Generando {num_samples} comentarios de feedback...")
        
        # Distribución de sentimientos (realista)
        sentiments = (
            ["POSITIVE"] * int(num_samples * 0.40) +    # 40% positivos
            ["NEUTRAL"] * int(num_samples * 0.35) +     # 35% neutrales
            ["NEGATIVE"] * int(num_samples * 0.25)      # 25% negativos
        )
        random.shuffle(sentiments)
        
        # Fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        feedbacks = []
        for i in range(num_samples):
            sentiment = sentiments[i]
            
            # Generar timestamp aleatorio
            random_days = random.randint(0, (end_date - start_date).days)
            timestamp = start_date + timedelta(
                days=random_days,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Datos del feedback
            feedback = {
                "user_id": random.randint(1, 100),
                "route_id": random.randint(1, 10),
                "text": self.get_comment_by_sentiment(sentiment),
                "rating": self.get_rating_by_sentiment(sentiment),
                "sentiment": sentiment,
                "confidence": round(random.uniform(0.75, 0.98), 2),
                "timestamp": timestamp,
                "source": random.choice(["mobile_app", "web", "social_media"]),
                "category": random.choice(["puntualidad", "limpieza", "conductor", "comodidad", "general"]),
                "resolved": random.choice([True, False]) if sentiment == "NEGATIVE" else None,
            }
            
            feedbacks.append(feedback)
            
            # Log progreso
            if (i + 1) % 1000 == 0:
                logger.info(f"   Generados {i + 1} comentarios...")
        
        logger.info(f"✅ Generados {len(feedbacks)} comentarios")
        return feedbacks
    
    def insert_feedback(self, feedbacks):
        """Insertar feedback en MongoDB"""
        logger.info("💾 Insertando feedback en MongoDB...")
        
        result = self.db.user_feedback.insert_many(feedbacks)
        
        logger.info(f"✅ Insertados {len(result.inserted_ids)} documentos exitosamente")
    
    def verify_data(self):
        """Verificar datos insertados"""
        total = self.db.user_feedback.count_documents({})
        logger.info(f"📊 Total de comentarios en MongoDB: {total:,}")
        
        # Estadísticas por sentimiento
        for sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
            count = self.db.user_feedback.count_documents({"sentiment": sentiment})
            percentage = (count / total * 100) if total > 0 else 0
            logger.info(f"   {sentiment}: {count:,} ({percentage:.1f}%)")
        
        # Rating promedio
        pipeline = [
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
        ]
        result = list(self.db.user_feedback.aggregate(pipeline))
        if result:
            logger.info(f"   Rating promedio: {result[0]['avg_rating']:.2f}/5")
    
    def create_sample_ml_metadata(self):
        """Crear metadata de modelos ML"""
        logger.info("📝 Creando metadata de modelos ML...")
        
        models_metadata = [
            {
                "model_id": "lstm_demand_v1",
                "model_type": "LSTM",
                "version": "1.0.0",
                "trained_date": datetime.now(),
                "status": "production",
                "metrics": {
                    "mae": 5.2,
                    "rmse": 8.3,
                    "mape": 0.12,
                    "r2": 0.85
                },
                "hyperparameters": {
                    "epochs": 50,
                    "batch_size": 32,
                    "sequence_length": 24,
                    "lstm_units": [128, 64, 32],
                    "dropout": 0.2
                },
                "training_data": {
                    "samples": 43200,
                    "features": 10,
                    "date_range": "2024-05-10 to 2024-11-10"
                }
            },
            {
                "model_id": "bert_sentiment_v1",
                "model_type": "BERT",
                "version": "1.0.0",
                "trained_date": datetime.now(),
                "status": "production",
                "base_model": "nlptown/bert-base-multilingual-uncased-sentiment",
                "metrics": {
                    "accuracy": 0.87,
                    "f1_score": 0.85,
                    "precision": 0.86,
                    "recall": 0.84
                },
                "hyperparameters": {
                    "epochs": 5,
                    "learning_rate": 2e-5,
                    "max_length": 512,
                    "batch_size": 16
                },
                "training_data": {
                    "samples": 5000,
                    "positive": 2000,
                    "neutral": 1750,
                    "negative": 1250
                }
            },
            {
                "model_id": "dbscan_users_v1",
                "model_type": "DBSCAN",
                "version": "1.0.0",
                "trained_date": datetime.now(),
                "status": "production",
                "metrics": {
                    "silhouette_score": 0.58,
                    "num_clusters": 5,
                    "outliers_percent": 8.5
                },
                "hyperparameters": {
                    "eps": 0.5,
                    "min_samples": 5,
                    "metric": "euclidean"
                },
                "training_data": {
                    "samples": 10000,
                    "features": 8
                }
            }
        ]
        
        self.db.ml_models.insert_many(models_metadata)
        logger.info("✅ Metadata de modelos creada")


def main():
    """Función principal"""
    logger.info("🚀 Iniciando población de MongoDB con feedback sintético")
    
    # Crear generador
    generator = MongoDBFeedbackGenerator(host='localhost', port=27017)
    
    try:
        # Crear colecciones
        generator.create_collections()
        
        # Generar feedback (5000 comentarios, 6 meses)
        feedbacks = generator.generate_feedback(num_samples=5000, months=6)
        
        # Insertar datos
        generator.insert_feedback(feedbacks)
        
        # Verificar
        generator.verify_data()
        
        # Crear metadata de modelos
        generator.create_sample_ml_metadata()
        
        logger.info("🎉 ¡Proceso completado exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
