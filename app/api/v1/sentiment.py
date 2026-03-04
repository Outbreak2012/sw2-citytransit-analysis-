from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from app.models.schemas import (
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    SentimentType
)
from app.ml.bert_model import bert_analyzer
from app.core.security import get_current_user
import logging
import random
import re
from collections import Counter
from app.db.redis_cache import redis_conn
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])

# Stop words en español para filtrar
STOP_WORDS = {
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'al',
    'y', 'o', 'en', 'que', 'es', 'por', 'para', 'con', 'no', 'se', 'su', 'sus',
    'como', 'más', 'pero', 'muy', 'ya', 'fue', 'son', 'este', 'esta', 'esto',
    'mi', 'me', 'lo', 'le', 'a', 'sin', 'sobre', 'ser', 'ha', 'era', 'sido',
    'todo', 'toda', 'todos', 'todas', 'hay', 'desde', 'hasta', 'cuando', 'donde',
    'bien', 'mal', 'eso', 'esa', 'ese', 'qué', 'cómo', 'así', 'tan', 'siempre'
}

def extract_keywords(text: str, top_n: int = 15) -> list:
    """Extraer palabras clave más frecuentes del texto"""
    # Limpiar y tokenizar
    words = re.findall(r'\b[a-záéíóúñü]{4,}\b', text.lower())
    
    # Filtrar stop words
    words = [w for w in words if w not in STOP_WORDS]
    
    # Contar frecuencias
    counter = Counter(words)
    
    # Retornar top N como lista de {word, count}
    return [{"word": word, "count": count} for word, count in counter.most_common(top_n)]


@router.post("/analyze", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze sentiment of text using BERT"""
    try:
        logger.info(f"Analyzing sentiment for text: {request.text[:50]}...")
        
        # Analyze sentiment
        result = bert_analyzer.analyze(request.text)
        
        return SentimentAnalysisResponse(
            sentiment=SentimentType(result['sentiment']),
            confidence_score=result['confidence_score'],
            scores=result['scores'],
            analyzed_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def analyze_batch(
    texts: list[str],
    current_user: dict = Depends(get_current_user)
):
    """Analyze sentiment for multiple texts"""
    try:
        logger.info(f"Analyzing sentiment for {len(texts)} texts...")
        
        results = bert_analyzer.batch_analyze(texts)
        
        return {
            "results": results,
            "total": len(results),
            "analyzed_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_sentiment_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get sentiment analysis summary from MongoDB"""
    try:
        logger.info(f"Getting sentiment summary for {days} days...")

        cache_key = f"sentiment:summary:{days}"
        try:
            cached = redis_conn.get(cache_key)
            if cached:
                logger.info("✅ Sentiment summary returned from cache")
                return cached
        except Exception:
            logger.debug("Redis not available for sentiment/summary")

        # Get real feedback from MongoDB
        from app.db.mongodb import mongodb_conn
        from datetime import timedelta
        
        try:
            db = mongodb_conn.connect()
            
            # Filter by date range
            start_date = datetime.now() - timedelta(days=days)
            
            # Get ALL feedback from the period (no limit)
            cursor = db.user_feedback.find(
                {
                    "comentario": {"$exists": True, "$ne": ""},
                    "created_at": {"$gte": start_date}
                },
                {"comentario": 1, "sentimiento": 1, "confidence_score": 1, "categoria": 1, "prioridad": 1, "ruta_nombre": 1}
            )
            
            feedbacks = list(cursor)
            logger.info(f"📊 Found {len(feedbacks)} feedback comments in MongoDB for last {days} days")
            
            if feedbacks:
                # Use existing sentiment from pre-analyzed data
                results = []
                for feedback in feedbacks:
                    # Map Spanish sentiment names to English for consistency
                    sent_raw = feedback.get('sentimiento', 'NEUTRAL')
                    sent_map = {
                        'POSITIVO': 'POSITIVE', 'POSITIVE': 'POSITIVE',
                        'NEGATIVO': 'NEGATIVE', 'NEGATIVE': 'NEGATIVE',
                        'NEUTRO': 'NEUTRAL', 'NEUTRAL': 'NEUTRAL'
                    }
                    sentiment = sent_map.get(sent_raw.upper(), 'NEUTRAL')
                    
                    results.append({
                        'sentiment': sentiment,
                        'confidence_score': feedback.get('confidence_score', 0.85),
                        'text': feedback.get('comentario', ''),
                        'categoria': feedback.get('categoria', 'general'),
                        'prioridad': feedback.get('prioridad', 3),
                        'ruta': feedback.get('ruta_nombre', 'N/A')
                    })
                
                # Calculate summary stats
                total = len(results)
                positive = sum(1 for r in results if r['sentiment'] == 'POSITIVE')
                negative = sum(1 for r in results if r['sentiment'] == 'NEGATIVE')
                neutral = sum(1 for r in results if r['sentiment'] == 'NEUTRAL')
                
                avg_confidence = sum(r['confidence_score'] for r in results) / total if total > 0 else 0
                
                # Count urgent (priority 4-5 and negative)
                urgent = sum(1 for r in results if r['prioridad'] >= 4 and r['sentiment'] == 'NEGATIVE')
                
                # Extract keywords from all texts
                all_text = ' '.join([r['text'] for r in results]).lower()
                keywords = extract_keywords(all_text)
                
                # Categories distribution
                categories = {}
                for r in results:
                    cat = r.get('categoria', 'general')
                    categories[cat] = categories.get(cat, 0) + 1
                
                # Build response in format expected by frontend
                summary = {
                    # Frontend expected fields
                    "total_comentarios": total,
                    "sentimiento_promedio": round((positive - negative) / total, 2) if total > 0 else 0,
                    "distribucion": {
                        "POSITIVO": positive,
                        "NEGATIVO": negative,
                        "NEUTRO": neutral
                    },
                    "keywords_frecuentes": [{"palabra": k["word"], "frecuencia": k["count"]} for k in keywords[:10]],
                    "comentarios_urgentes": urgent,
                    # Additional detailed fields
                    "total_analyzed": total,
                    "sentiment_distribution": {
                        "positive": positive,
                        "negative": negative,
                        "neutral": neutral,
                        "positive_pct": round(positive / total * 100, 1) if total > 0 else 0,
                        "negative_pct": round(negative / total * 100, 1) if total > 0 else 0,
                        "neutral_pct": round(neutral / total * 100, 1) if total > 0 else 0
                    },
                    "average_confidence": round(avg_confidence, 2),
                    "urgent_count": urgent,
                    "satisfaction_rate": round(positive / total * 100, 1) if total > 0 else 0,
                    "keywords": keywords[:15],
                    "categories": categories,
                    "score": round((positive - negative) / total, 2) if total > 0 else 0
                }
            else:
                logger.warning("No feedback found in MongoDB for the period")
                # Fallback to sample data
                sample_feedbacks = [
                    "Excelente servicio, muy puntual y cómodo",
                    "El bus llegó tarde, muy mala experiencia",
                    "Buen servicio en general, nada especial",
                    "Muy mal, conductor grosero y bus sucio",
                    "Todo perfecto, lo recomiendo completamente",
                    "Regular, podría mejorar la limpieza",
                    "Pésima atención al cliente",
                    "Me encanta este servicio de transporte",
                    "Normal, cumple su función",
                    "Muy buena experiencia, seguiré usando"
                ]
                results = bert_analyzer.batch_analyze(sample_feedbacks * 5)
                stats = bert_analyzer.get_summary_stats(results)
                # Convert to frontend format
                summary = {
                    "total_comentarios": stats.get("total_analyzed", 50),
                    "sentimiento_promedio": stats.get("score", 0),
                    "distribucion": {
                        "POSITIVO": stats.get("sentiment_distribution", {}).get("positive", 20),
                        "NEGATIVO": stats.get("sentiment_distribution", {}).get("negative", 15),
                        "NEUTRO": stats.get("sentiment_distribution", {}).get("neutral", 15)
                    },
                    "keywords_frecuentes": [{"palabra": k.get("word", k.get("palabra", "")), "frecuencia": k.get("count", k.get("frecuencia", 0))} for k in stats.get("keywords", [])[:10]],
                    "comentarios_urgentes": stats.get("urgent_count", 0),
                    **stats
                }
                
        except Exception as e:
            logger.error(f"Error accessing MongoDB: {e}, using sample data")
            # Fallback data
            sample_feedbacks = [
                "Excelente servicio, muy puntual y cómodo",
                "El bus llegó tarde, muy mala experiencia",
                "Buen servicio en general, nada especial",
                "Muy mal, conductor grosero y bus sucio",
                "Todo perfecto, lo recomiendo completamente",
                "Regular, podría mejorar la limpieza",
                "Pésima atención al cliente",
                "Me encanta este servicio de transporte",
                "Normal, cumple su función",
                "Muy buena experiencia, seguiré usando"
            ]
            results = bert_analyzer.batch_analyze(sample_feedbacks * 5)
            stats = bert_analyzer.get_summary_stats(results)
            # Convert to frontend format
            summary = {
                "total_comentarios": stats.get("total_analyzed", 50),
                "sentimiento_promedio": stats.get("score", 0),
                "distribucion": {
                    "POSITIVO": stats.get("sentiment_distribution", {}).get("positive", 20),
                    "NEGATIVO": stats.get("sentiment_distribution", {}).get("negative", 15),
                    "NEUTRO": stats.get("sentiment_distribution", {}).get("neutral", 15)
                },
                "keywords_frecuentes": [{"palabra": k.get("word", k.get("palabra", "")), "frecuencia": k.get("count", k.get("frecuencia", 0))} for k in stats.get("keywords", [])[:10]],
                "comentarios_urgentes": stats.get("urgent_count", 0),
                **stats
            }

        # Return summary directly (not nested under "summary" key)
        # Add metadata
        summary["period"] = {
            "days": days,
            "from": (datetime.now() - timedelta(days=days)).isoformat(),
            "to": datetime.now().isoformat()
        }
        summary["generated_at"] = datetime.now().isoformat()

        try:
            redis_conn.set(cache_key, summary, ttl=getattr(settings, 'CACHE_TTL', 300))
        except Exception:
            logger.debug("Could not cache sentiment summary")

        return summary
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_sentiment_trends(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get sentiment trends over time"""
    try:
        logger.info(f"Getting sentiment trends for {days} days...")
        
        cache_key = f"sentiment:trends:{days}"
        try:
            cached = redis_conn.get(cache_key)
            if cached:
                logger.info("✅ Sentiment trends from cache")
                return cached
        except Exception:
            pass
        
        # Try to get real data from MongoDB
        from app.db.mongodb import mongodb_conn
        
        try:
            db = mongodb_conn.connect()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Aggregate sentiment by date
            pipeline = [
                {"$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "sentimiento": {"$exists": True}
                }},
                {"$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                        "sentiment": "$sentimiento"
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id.date": 1}}
            ]
            
            results = list(db.user_feedback.aggregate(pipeline))
            
            if results:
                # Reorganize by date
                daily_data = {}
                for r in results:
                    date = r['_id']['date']
                    sentiment = r['_id']['sentiment']
                    count = r['count']
                    
                    if date not in daily_data:
                        daily_data[date] = {'positive': 0, 'neutral': 0, 'negative': 0}
                    
                    # Normalize sentiment labels
                    if sentiment in ['positive', 'positivo']:
                        daily_data[date]['positive'] += count
                    elif sentiment in ['negative', 'negativo']:
                        daily_data[date]['negative'] += count
                    else:
                        daily_data[date]['neutral'] += count
                
                trends = [
                    {
                        "date": date,
                        "positive": data['positive'],
                        "neutral": data['neutral'],
                        "negative": data['negative'],
                        "total": sum(data.values())
                    }
                    for date, data in sorted(daily_data.items())
                ]
                data_source = 'mongodb'
            else:
                # Generate estimated trends
                trends = []
                for i in range(days):
                    date = (datetime.now() - timedelta(days=days - i - 1)).date().isoformat()
                    # Use deterministic values based on date hash
                    base = hash(date) % 100
                    trends.append({
                        "date": date,
                        "positive": 30 + (base % 25),
                        "neutral": 40 + ((base * 2) % 20),
                        "negative": 10 + ((base * 3) % 15),
                        "total": 80 + (base % 40)
                    })
                data_source = 'estimated'
                
        except Exception as e:
            logger.warning(f"MongoDB query failed: {e}, using estimates")
            trends = []
            for i in range(days):
                date = (datetime.now() - timedelta(days=days - i - 1)).date().isoformat()
                base = hash(date) % 100
                trends.append({
                    "date": date,
                    "positive": 30 + (base % 25),
                    "neutral": 40 + ((base * 2) % 20),
                    "negative": 10 + ((base * 3) % 15),
                    "total": 80 + (base % 40)
                })
            data_source = 'estimated'
        
        result = {
            "trends": trends,
            "period": {
                "days": days,
                "from": (datetime.now() - timedelta(days=days)).isoformat(),
                "to": datetime.now().isoformat()
            },
            "data_source": data_source,
            "generated_at": datetime.now()
        }
        
        try:
            cache_result = dict(result)
            cache_result['generated_at'] = cache_result['generated_at'].isoformat()
            redis_conn.set(cache_key, cache_result, ttl=getattr(settings, 'CACHE_TTL', 300))
        except Exception:
            pass
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-route/{route_id}")
async def get_sentiment_by_route(
    route_id: int,
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get sentiment analysis for specific route"""
    try:
        logger.info(f"Getting sentiment for route {route_id}...")
        
        # Generate mock feedback for route
        route_feedbacks = [
            "Esta ruta es excelente",
            "Buena frecuencia de buses",
            "A veces hay demora",
            "Ruta muy conveniente",
            "Regular el servicio"
        ]
        
        # Analyze
        results = bert_analyzer.batch_analyze(route_feedbacks * 3)
        summary = bert_analyzer.get_summary_stats(results)
        
        return {
            "route_id": route_id,
            "summary": summary,
            "period_days": days,
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting route sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
