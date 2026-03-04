"""
BERT Sentiment Analyzer para CityTransit
=========================================
Análisis de sentimientos usando modelos BERT en español.
Usa PyTorch para evitar conflictos con Keras 3.
"""
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

# Intentar importar PyTorch y Transformers
try:
    import torch
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    HAS_TRANSFORMERS = True
    DEVICE = 0 if torch.cuda.is_available() else -1
    logger.info(f"✅ PyTorch disponible. Device: {'CUDA' if DEVICE == 0 else 'CPU'}")
except ImportError as e:
    HAS_TRANSFORMERS = False
    DEVICE = -1
    logger.warning(f"⚠️ PyTorch/Transformers no disponible: {e}")


class BERTSentimentAnalyzer:
    """
    Analizador de sentimientos usando BERT.
    Soporta múltiples modelos de respaldo.
    """
    
    # Modelos ordenados por preferencia (español primero)
    MODELS = [
        "nlptown/bert-base-multilingual-uncased-sentiment",  # Multilingüe 5 estrellas
        "cardiffnlp/twitter-xlm-roberta-base-sentiment",     # XLM-RoBERTa multilingüe
        "distilbert-base-uncased-finetuned-sst-2-english",   # Fallback inglés (más rápido)
    ]
    
    # Templates de feedback de transporte para generar datos sintéticos
    FEEDBACK_TEMPLATES = {
        'positive': [
            "Excelente servicio, el bus llegó puntual",
            "Muy buen viaje, el conductor fue muy amable",
            "Me encanta este sistema de transporte, es muy eficiente",
            "El micro estaba limpio y cómodo, recomendado",
            "Llegué a tiempo gracias al transporte público",
            "Servicio de primera, muy satisfecho",
            "Chévere el nuevo sistema de tarjetas",
            "El aire acondicionado funcionaba perfecto",
            "Muy seguro el viaje, el conductor respetó las normas",
            "La app funciona muy bien, fácil de usar",
        ],
        'negative': [
            "Pésimo servicio, el bus nunca llegó",
            "Muy mal, el conductor fue grosero",
            "El micro estaba sucio y maloliente",
            "Llegué tarde por culpa del transporte",
            "Demasiado caro para lo que ofrecen",
            "No sirve este sistema, siempre demora",
            "El aire acondicionado no funcionaba",
            "Inseguro, había mucha gente y nadie controlaba",
            "La tarjeta no me funcionó, perdí mi pasaje",
            "Queja formal por el maltrato del personal",
        ],
        'neutral': [
            "El servicio estuvo normal, nada especial",
            "Llegó más o menos a tiempo",
            "El viaje fue regular",
            "No tengo quejas pero tampoco elogios",
            "Funcionó como siempre",
            "El bus pasó, eso es todo",
            "Normal el servicio de hoy",
            "Sin comentarios particulares",
            "Como cualquier otro día",
            "Ni bueno ni malo",
        ]
    }
    
    def __init__(self):
        self.pipeline = None
        self.model_name = None
        self.is_loaded = False
        self.config_path = getattr(settings, 'BERT_CONFIG_PATH', 'models/bert_config.json')
        self.analysis_history: List[Dict] = []
        self.total_analyzed = 0
        self.load_timestamp = None
        
    def load_model(self) -> bool:
        """
        Cargar modelo BERT. Intenta varios modelos en orden de preferencia.
        Returns: True si se cargó exitosamente, False si usa fallback.
        """
        if not HAS_TRANSFORMERS:
            logger.warning("⚠️ Transformers no disponible. Usando análisis basado en reglas.")
            return False
        
        for model_name in self.MODELS:
            try:
                logger.info(f"🤖 Intentando cargar modelo: {model_name}")
                
                # Usar pipeline de sentiment-analysis con PyTorch
                self.pipeline = pipeline(
                    task="sentiment-analysis",
                    model=model_name,
                    device=DEVICE,
                    framework="pt",  # Forzar PyTorch
                    truncation=True,
                    max_length=512
                )
                
                # Verificar que funciona con un texto de prueba
                test_result = self.pipeline("Prueba de funcionamiento")
                
                self.model_name = model_name
                self.is_loaded = True
                self.load_timestamp = datetime.now().isoformat()
                logger.info(f"✅ Modelo BERT cargado exitosamente: {model_name}")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ No se pudo cargar {model_name}: {e}")
                continue
        
        logger.warning("⚠️ Ningún modelo BERT disponible. Usando análisis basado en reglas.")
        return False
    
    def analyze(self, text: str) -> Dict:
        """
        Analizar sentimiento de un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con sentiment, confidence_score y scores detallados
        """
        if not text or not text.strip():
            return self._empty_result()
        
        # Limpiar texto
        text = self._clean_text(text)
        
        # Intentar usar modelo BERT
        if self.pipeline is None and HAS_TRANSFORMERS:
            self.load_model()
        
        if self.pipeline is not None:
            try:
                return self._bert_analyze(text)
            except Exception as e:
                logger.error(f"❌ Error en análisis BERT: {e}")
        
        # Fallback a análisis basado en reglas
        return self._rule_based_analyze(text)
    
    def _bert_analyze(self, text: str) -> Dict:
        """Análisis usando modelo BERT"""
        result = self.pipeline(text[:512])[0]
        
        # Mapear labels según el modelo
        sentiment, confidence = self._map_result(result)
        
        # Generar scores detallados
        scores = self._generate_scores(sentiment, confidence)
        
        return {
            "sentiment": sentiment,
            "confidence_score": confidence,
            "scores": scores,
            "model": self.model_name,
            "method": "bert"
        }
    
    def _map_result(self, result: Dict) -> tuple:
        """Mapear resultado del modelo a nuestras categorías"""
        label = result.get('label', '').upper()
        score = float(result.get('score', 0.5))
        
        # Mapeo para modelo de 5 estrellas (nlptown)
        star_mapping = {
            "1 STAR": ("NEGATIVE", score),
            "2 STARS": ("NEGATIVE", score * 0.8),
            "3 STARS": ("NEUTRAL", score),
            "4 STARS": ("POSITIVE", score * 0.8),
            "5 STARS": ("POSITIVE", score),
        }
        
        # Mapeo para modelos de sentimiento directo
        direct_mapping = {
            "POSITIVE": ("POSITIVE", score),
            "NEGATIVE": ("NEGATIVE", score),
            "NEUTRAL": ("NEUTRAL", score),
            "LABEL_0": ("NEGATIVE", score),  # cardiffnlp
            "LABEL_1": ("NEUTRAL", score),
            "LABEL_2": ("POSITIVE", score),
        }
        
        if label in star_mapping:
            return star_mapping[label]
        elif label in direct_mapping:
            return direct_mapping[label]
        else:
            # Intentar inferir del label
            if 'POS' in label or 'GOOD' in label:
                return ("POSITIVE", score)
            elif 'NEG' in label or 'BAD' in label:
                return ("NEGATIVE", score)
            return ("NEUTRAL", score)
    
    def _generate_scores(self, sentiment: str, confidence: float) -> Dict:
        """Generar scores detallados para cada categoría"""
        remaining = 1.0 - confidence
        
        if sentiment == "POSITIVE":
            return {
                "positive": confidence,
                "neutral": remaining * 0.7,
                "negative": remaining * 0.3
            }
        elif sentiment == "NEGATIVE":
            return {
                "positive": remaining * 0.3,
                "neutral": remaining * 0.7,
                "negative": confidence
            }
        else:
            return {
                "positive": remaining * 0.5,
                "neutral": confidence,
                "negative": remaining * 0.5
            }
    
    def _rule_based_analyze(self, text: str) -> Dict:
        """
        Análisis de sentimiento basado en reglas para español boliviano.
        Incluye modismos y expresiones locales de Santa Cruz.
        """
        text_lower = text.lower()
        
        # Keywords positivas (español boliviano/cruceño)
        positive_words = [
            # Generales
            'excelente', 'bueno', 'genial', 'perfecto', 'increíble', 'fantástico',
            'maravilloso', 'espectacular', 'hermoso', 'lindo', 'bien', 'mejor',
            'feliz', 'contento', 'satisfecho', 'encantado', 'agradecido',
            # Transporte específico
            'puntual', 'rápido', 'eficiente', 'cómodo', 'limpio', 'seguro',
            'confiable', 'práctico', 'económico', 'accesible',
            # Expresiones bolivianas/cruceñas
            'chévere', 'bacán', 'pucha que bueno', 'está yesca', 'de lujo',
            'recomiendo', 'gracias', 'felicitaciones', 'excelente servicio'
        ]
        
        # Keywords negativas
        negative_words = [
            # Generales
            'malo', 'pésimo', 'horrible', 'terrible', 'fatal', 'desastre',
            'peor', 'odio', 'nunca', 'jamás', 'decepcionado', 'frustrado',
            # Transporte específico
            'tarde', 'tardó', 'demora', 'demoró', 'atrasado', 'cancelado',
            'sucio', 'grosero', 'irrespetuoso', 'peligroso', 'inseguro',
            'incómodo', 'caro', 'lento', 'perdido', 'roto', 'dañado',
            # Quejas
            'queja', 'reclamo', 'problema', 'error', 'falla', 'deficiente',
            # Expresiones bolivianas
            'qué porquería', 'malísimo', 'no sirve', 'un asco', 'pésimo servicio'
        ]
        
        # Intensificadores
        intensifiers = ['muy', 'super', 'demasiado', 'bastante', 'extremadamente', 'totalmente']
        
        # Negadores que invierten el sentimiento
        negators = ['no', 'nunca', 'jamás', 'tampoco', 'ni', 'sin']
        
        # Contar matches con peso
        positive_score = 0
        negative_score = 0
        
        words = text_lower.split()
        
        for i, word in enumerate(words):
            # Verificar si hay negador antes
            has_negator = i > 0 and words[i-1] in negators
            
            # Verificar intensificador
            has_intensifier = i > 0 and words[i-1] in intensifiers
            weight = 1.5 if has_intensifier else 1.0
            
            # Buscar matches parciales
            for pos_word in positive_words:
                if pos_word in word or word in pos_word:
                    if has_negator:
                        negative_score += weight
                    else:
                        positive_score += weight
                    break
            
            for neg_word in negative_words:
                if neg_word in word or word in neg_word:
                    if has_negator:
                        positive_score += weight * 0.5  # Doble negación es menos positiva
                    else:
                        negative_score += weight
                    break
        
        # Determinar sentimiento final
        total = positive_score + negative_score
        
        if total == 0:
            sentiment = "NEUTRAL"
            confidence = 0.6
        elif positive_score > negative_score * 1.2:
            sentiment = "POSITIVE"
            confidence = min(0.55 + (positive_score / (total + 1)) * 0.4, 0.92)
        elif negative_score > positive_score * 1.2:
            sentiment = "NEGATIVE"
            confidence = min(0.55 + (negative_score / (total + 1)) * 0.4, 0.92)
        else:
            sentiment = "NEUTRAL"
            confidence = 0.65
        
        scores = self._generate_scores(sentiment, confidence)
        
        return {
            "sentiment": sentiment,
            "confidence_score": round(confidence, 4),
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "model": "rule-based-spanish-bo",
            "method": "rules"
        }
    
    def _clean_text(self, text: str) -> str:
        """Limpiar y normalizar texto"""
        # Remover URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        # Remover menciones y hashtags
        text = re.sub(r'[@#]\w+', '', text)
        # Remover caracteres especiales excesivos
        text = re.sub(r'[!?]{2,}', '!', text)
        # Normalizar espacios
        text = ' '.join(text.split())
        return text.strip()
    
    def _empty_result(self) -> Dict:
        """Resultado para texto vacío"""
        return {
            "sentiment": "NEUTRAL",
            "confidence_score": 0.0,
            "scores": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
            "model": None,
            "method": "empty"
        }
    
    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """
        Analizar múltiples textos.
        
        Args:
            texts: Lista de textos a analizar
            
        Returns:
            Lista de resultados de análisis
        """
        if not texts:
            return []
        
        # Si tenemos pipeline BERT, usar batch processing
        if self.pipeline is not None:
            try:
                cleaned_texts = [self._clean_text(t)[:512] for t in texts if t]
                results = self.pipeline(cleaned_texts)
                
                analyzed = []
                for result in results:
                    sentiment, confidence = self._map_result(result)
                    scores = self._generate_scores(sentiment, confidence)
                    analyzed.append({
                        "sentiment": sentiment,
                        "confidence_score": confidence,
                        "scores": scores,
                        "model": self.model_name,
                        "method": "bert"
                    })
                
                logger.info(f"✅ Analizados {len(analyzed)} textos con BERT")
                return analyzed
                
            except Exception as e:
                logger.error(f"❌ Error en batch BERT: {e}")
        
        # Fallback: analizar uno por uno con reglas
        results = [self.analyze(text) for text in texts]
        logger.info(f"✅ Analizados {len(results)} textos con reglas")
        return results
    
    def get_summary_stats(self, sentiments: List[Dict]) -> Dict:
        """
        Obtener estadísticas resumen de análisis de sentimientos.
        
        Args:
            sentiments: Lista de resultados de análisis
            
        Returns:
            Dict con estadísticas agregadas
        """
        if not sentiments:
            return {
                "total": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "positive_ratio": 0.0,
                "neutral_ratio": 0.0,
                "negative_ratio": 0.0,
                "avg_confidence": 0.0,
                "method_breakdown": {}
            }
        
        total = len(sentiments)
        positive = sum(1 for s in sentiments if s.get('sentiment') == 'POSITIVE')
        neutral = sum(1 for s in sentiments if s.get('sentiment') == 'NEUTRAL')
        negative = sum(1 for s in sentiments if s.get('sentiment') == 'NEGATIVE')
        avg_confidence = sum(s.get('confidence_score', 0) for s in sentiments) / total
        
        # Desglose por método
        methods = {}
        for s in sentiments:
            method = s.get('method', 'unknown')
            methods[method] = methods.get(method, 0) + 1
        
        return {
            "total": total,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "positive_ratio": round(positive / total, 4),
            "neutral_ratio": round(neutral / total, 4),
            "negative_ratio": round(negative / total, 4),
            "avg_confidence": round(avg_confidence, 4),
            "method_breakdown": methods
        }
    
    def get_model_info(self) -> Dict:
        """Obtener información del modelo actual"""
        return {
            "is_loaded": self.is_loaded,
            "model_name": self.model_name,
            "has_transformers": HAS_TRANSFORMERS,
            "device": "cuda" if DEVICE == 0 else "cpu",
            "available_models": self.MODELS,
            "load_timestamp": self.load_timestamp,
            "total_analyzed": self.total_analyzed,
            "config_path": self.config_path
        }
    
    # ==================== NUEVAS FUNCIONALIDADES ====================
    
    def save_config(self, path: Optional[str] = None) -> str:
        """Guardar configuración y estado del analizador
        
        Args:
            path: Ruta personalizada (opcional)
            
        Returns:
            Ruta donde se guardó la configuración
        """
        save_path = path or self.config_path
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        
        config = {
            'model_name': self.model_name,
            'is_loaded': self.is_loaded,
            'load_timestamp': self.load_timestamp,
            'total_analyzed': self.total_analyzed,
            'available_models': self.MODELS,
            'has_transformers': HAS_TRANSFORMERS,
            'device': 'cuda' if DEVICE == 0 else 'cpu',
            'saved_at': datetime.now().isoformat()
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Configuración guardada en {save_path}")
        return save_path
    
    def load_config(self, path: Optional[str] = None) -> bool:
        """Cargar configuración desde archivo
        
        Args:
            path: Ruta personalizada (opcional)
            
        Returns:
            True si se cargó exitosamente
        """
        load_path = path or self.config_path
        
        if not os.path.exists(load_path):
            logger.warning(f"⚠️ Archivo de configuración no encontrado: {load_path}")
            return False
        
        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.total_analyzed = config.get('total_analyzed', 0)
            
            # Si hay un modelo guardado, intentar cargarlo
            saved_model = config.get('model_name')
            if saved_model and HAS_TRANSFORMERS:
                logger.info(f"📥 Intentando cargar modelo guardado: {saved_model}")
                # Mover el modelo preferido al inicio de la lista
                if saved_model in self.MODELS:
                    self.MODELS.remove(saved_model)
                    self.MODELS.insert(0, saved_model)
                self.load_model()
            
            logger.info(f"✅ Configuración cargada desde {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            return False
    
    def generate_training_data(self, num_samples: int = 300, 
                                balanced: bool = True) -> List[Dict[str, Any]]:
        """Generar datos sintéticos de feedback de transporte para entrenamiento
        
        Args:
            num_samples: Número total de muestras a generar
            balanced: Si True, genera igual cantidad de cada sentimiento
            
        Returns:
            Lista de diccionarios con 'text' y 'label'
        """
        logger.info(f"📊 Generando {num_samples} muestras de entrenamiento...")
        
        data = []
        
        if balanced:
            samples_per_class = num_samples // 3
            for sentiment in ['positive', 'negative', 'neutral']:
                templates = self.FEEDBACK_TEMPLATES[sentiment]
                for _ in range(samples_per_class):
                    # Seleccionar template y agregar variación
                    base_text = random.choice(templates)
                    text = self._add_variation(base_text, sentiment)
                    data.append({
                        'text': text,
                        'label': sentiment.upper(),
                        'generated_at': datetime.now().isoformat()
                    })
        else:
            # Distribución realista: 60% neutral, 25% positive, 15% negative
            distribution = {
                'neutral': int(num_samples * 0.6),
                'positive': int(num_samples * 0.25),
                'negative': int(num_samples * 0.15)
            }
            for sentiment, count in distribution.items():
                templates = self.FEEDBACK_TEMPLATES[sentiment]
                for _ in range(count):
                    base_text = random.choice(templates)
                    text = self._add_variation(base_text, sentiment)
                    data.append({
                        'text': text,
                        'label': sentiment.upper(),
                        'generated_at': datetime.now().isoformat()
                    })
        
        random.shuffle(data)
        logger.info(f"✅ Generadas {len(data)} muestras de entrenamiento")
        return data
    
    def _add_variation(self, text: str, sentiment: str) -> str:
        """Agregar variación a un texto template
        
        Args:
            text: Texto base
            sentiment: Sentimiento del texto
            
        Returns:
            Texto con variaciones
        """
        # Variaciones comunes
        prefixes = {
            'positive': ['¡', 'Muy ', 'Realmente ', 'Súper ', ''],
            'negative': ['¡', 'Muy ', 'Demasiado ', 'Súper ', 'Totalmente '],
            'neutral': ['Bueno, ', 'Pues ', 'En fin, ', '']
        }
        
        suffixes = {
            'positive': ['.', '!', ' 👍', ' :)', ' ⭐'],
            'negative': ['.', '!', ' 👎', ' :(', ' 😤'],
            'neutral': ['.', '', ' 🤷', ' ok']
        }
        
        # Rutas aleatorias
        routes = ['Ruta 1', 'Ruta 5', 'Línea 12', 'Micro 45', 'Bus 23', '']
        
        # Construir texto con variaciones
        prefix = random.choice(prefixes.get(sentiment, ['']))
        suffix = random.choice(suffixes.get(sentiment, ['.']))
        route = random.choice(routes)
        
        if route and random.random() > 0.5:
            text = f"{text} ({route})"
        
        return f"{prefix}{text}{suffix}"
    
    def evaluate_accuracy(self, test_data: List[Dict[str, str]]) -> Dict[str, Any]:
        """Evaluar precisión del modelo con datos de prueba
        
        Args:
            test_data: Lista de dicts con 'text' y 'label'
            
        Returns:
            Dict con métricas de evaluación
        """
        if not test_data:
            return {'error': 'No test data provided'}
        
        logger.info(f"📊 Evaluando modelo con {len(test_data)} muestras...")
        
        correct = 0
        total = len(test_data)
        confusion = {
            'POSITIVE': {'POSITIVE': 0, 'NEUTRAL': 0, 'NEGATIVE': 0},
            'NEUTRAL': {'POSITIVE': 0, 'NEUTRAL': 0, 'NEGATIVE': 0},
            'NEGATIVE': {'POSITIVE': 0, 'NEUTRAL': 0, 'NEGATIVE': 0}
        }
        
        for item in test_data:
            text = item.get('text', '')
            true_label = item.get('label', '').upper()
            
            if true_label not in confusion:
                continue
            
            result = self.analyze(text)
            pred_label = result.get('sentiment', 'NEUTRAL')
            
            confusion[true_label][pred_label] += 1
            if pred_label == true_label:
                correct += 1
        
        accuracy = correct / total if total > 0 else 0
        
        # Calcular precision, recall, f1 por clase
        metrics_per_class = {}
        for label in ['POSITIVE', 'NEUTRAL', 'NEGATIVE']:
            tp = confusion[label][label]
            fp = sum(confusion[other][label] for other in confusion if other != label)
            fn = sum(confusion[label][other] for other in confusion[label] if other != label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            metrics_per_class[label] = {
                'precision': round(precision, 4),
                'recall': round(recall, 4),
                'f1': round(f1, 4)
            }
        
        result = {
            'accuracy': round(accuracy, 4),
            'total_samples': total,
            'correct_predictions': correct,
            'confusion_matrix': confusion,
            'metrics_per_class': metrics_per_class,
            'model_used': self.model_name or 'rule-based',
            'method': 'bert' if self.is_loaded else 'rules'
        }
        
        logger.info(f"✅ Evaluación completada. Accuracy: {accuracy:.2%}")
        return result
    
    def analyze_with_tracking(self, text: str) -> Dict:
        """Analizar texto con seguimiento de historial
        
        Args:
            text: Texto a analizar
            
        Returns:
            Resultado del análisis
        """
        result = self.analyze(text)
        
        # Tracking
        self.total_analyzed += 1
        self.analysis_history.append({
            'timestamp': datetime.now().isoformat(),
            'text_length': len(text),
            'sentiment': result.get('sentiment'),
            'confidence': result.get('confidence_score'),
            'method': result.get('method')
        })
        
        # Mantener solo últimos 1000 registros
        if len(self.analysis_history) > 1000:
            self.analysis_history = self.analysis_history[-1000:]
        
        return result
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de análisis realizados
        
        Returns:
            Dict con estadísticas de uso
        """
        if not self.analysis_history:
            return {
                'total_analyzed': self.total_analyzed,
                'recent_analyses': 0,
                'sentiment_distribution': {},
                'method_distribution': {},
                'avg_confidence': 0
            }
        
        sentiments = [h['sentiment'] for h in self.analysis_history]
        methods = [h['method'] for h in self.analysis_history]
        confidences = [h['confidence'] for h in self.analysis_history if h['confidence']]
        
        return {
            'total_analyzed': self.total_analyzed,
            'recent_analyses': len(self.analysis_history),
            'sentiment_distribution': {
                'POSITIVE': sentiments.count('POSITIVE'),
                'NEUTRAL': sentiments.count('NEUTRAL'),
                'NEGATIVE': sentiments.count('NEGATIVE')
            },
            'method_distribution': {
                'bert': methods.count('bert'),
                'rules': methods.count('rules')
            },
            'avg_confidence': round(sum(confidences) / len(confidences), 4) if confidences else 0
        }


# Instancia global
bert_analyzer = BERTSentimentAnalyzer()
