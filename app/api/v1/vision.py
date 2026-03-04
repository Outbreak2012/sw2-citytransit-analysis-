"""
API de Visión Artificial - Detección de Ocupación Vehicular
============================================================
Endpoints para analizar imágenes de cámaras de seguridad
y detectar el nivel de ocupación de vehículos usando TensorFlow.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np
import logging
import base64

from app.ml.vision_model import vision_model, OCCUPANCY_CLASSES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Computer Vision"])


# === Modelos de Request/Response ===

class VisionAnalysisRequest(BaseModel):
    """Request para análisis de imagen en base64."""
    image_base64: str
    vehicle_id: Optional[int] = 0
    route_id: Optional[int] = None


class SimulatedAnalysisRequest(BaseModel):
    """Request para análisis simulado (demo/testing)."""
    vehicle_id: int = 1
    simulated_occupancy: Optional[float] = None  # 0.0 a 1.0


class BatchAnalysisRequest(BaseModel):
    """Request para análisis en batch."""
    vehicle_ids: List[int]


class TrainRequest(BaseModel):
    """Request para entrenar el modelo."""
    epochs: int = 15
    batch_size: int = 32
    num_samples: int = 1800


# === Endpoints ===

@router.get("/model-info")
async def get_model_info():
    """
    Información del modelo de visión artificial.
    
    Retorna detalles sobre:
    - Arquitectura (MobileNetV2 + Custom Head)
    - Framework (TensorFlow 2.x)
    - Clases de detección
    - Estado del modelo
    - Pipeline de entrenamiento
    """
    return {
        "status": "active",
        "model": vision_model.get_model_info(),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/analyze")
async def analyze_image(request: VisionAnalysisRequest):
    """
    Analizar una imagen para detectar nivel de ocupación.
    
    Recibe imagen en base64, la procesa con el modelo MobileNetV2
    y retorna:
    - Nivel de ocupación (VACIO → SOBRECARGADO)
    - Personas detectadas
    - Porcentaje de ocupación
    - Alertas automáticas
    - Probabilidades por clase
    """
    try:
        # Decodificar base64
        image_data = base64.b64decode(request.image_base64)
        
        # Analizar con modelo
        result = vision_model.analyze_frame(image_data, request.vehicle_id)
        
        if request.route_id:
            result["ruta_id"] = request.route_id
        
        return result
        
    except Exception as e:
        logger.error(f"Error en análisis de imagen: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando imagen: {str(e)}")


@router.post("/analyze-upload")
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    vehicle_id: int = Query(default=0, description="ID del vehículo")
):
    """
    Analizar imagen subida directamente (multipart/form-data).
    
    Acepta formatos: JPEG, PNG, BMP
    Procesa con MobileNetV2 para clasificar ocupación.
    """
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
        
        image_data = await file.read()
        result = vision_model.analyze_frame(image_data, vehicle_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/analyze-simulated")
async def analyze_simulated(request: SimulatedAnalysisRequest):
    """
    Análisis simulado para demo y testing.
    
    Genera una imagen sintética de bus con el nivel de ocupación
    especificado y la procesa con el modelo.
    Útil para demostrar la funcionalidad sin cámaras reales.
    """
    try:
        if request.simulated_occupancy is not None:
            # Determinar nivel basado en ocupación
            occ = request.simulated_occupancy
            if occ < 0.10:
                level = 0
            elif occ < 0.30:
                level = 1
            elif occ < 0.60:
                level = 2
            elif occ < 0.80:
                level = 3
            elif occ < 0.95:
                level = 4
            else:
                level = 5
        else:
            level = np.random.randint(0, 6)
        
        # Generar imagen sintética
        synthetic_image = vision_model._generate_synthetic_bus_image(level)
        
        # Desnormalizar de [-1,1] a [0,1] para predicción
        image_for_predict = (synthetic_image + 1.0) / 2.0
        
        # Predecir
        result = vision_model.predict(image_for_predict)
        result["vehiculo_id"] = request.vehicle_id
        result["simulated"] = True
        result["requested_occupancy_level"] = OCCUPANCY_CLASSES[level]
        
        return result
        
    except Exception as e:
        logger.error(f"Error en análisis simulado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze")
async def batch_analyze(request: BatchAnalysisRequest):
    """
    Análisis en batch de múltiples vehículos.
    
    Simula el análisis de imágenes de cámaras de seguridad
    de múltiples vehículos simultáneamente.
    """
    try:
        results = []
        for vehicle_id in request.vehicle_ids:
            # Generar imagen sintética para cada vehículo
            level = np.random.randint(0, 6)
            synthetic_image = vision_model._generate_synthetic_bus_image(level)
            image_for_predict = (synthetic_image + 1.0) / 2.0
            
            result = vision_model.predict(image_for_predict)
            result["vehiculo_id"] = vehicle_id
            results.append(result)
        
        # Resumen
        avg_occupancy = np.mean([r["porcentajeOcupacion"] for r in results])
        critical_vehicles = [r for r in results if r["nivelOcupacion"] in ["LLENO", "SOBRECARGADO"]]
        
        return {
            "total_analyzed": len(results),
            "avg_occupancy": round(float(avg_occupancy), 4),
            "critical_vehicles": len(critical_vehicles),
            "results": results,
            "summary": {
                "VACIO": len([r for r in results if r["nivelOcupacion"] == "VACIO"]),
                "BAJO": len([r for r in results if r["nivelOcupacion"] == "BAJO"]),
                "MEDIO": len([r for r in results if r["nivelOcupacion"] == "MEDIO"]),
                "ALTO": len([r for r in results if r["nivelOcupacion"] == "ALTO"]),
                "LLENO": len([r for r in results if r["nivelOcupacion"] == "LLENO"]),
                "SOBRECARGADO": len([r for r in results if r["nivelOcupacion"] == "SOBRECARGADO"]),
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en batch analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_model(request: TrainRequest):
    """
    Entrenar/re-entrenar el modelo de visión artificial.
    
    Genera datos sintéticos, aplica data augmentation,
    y entrena el modelo MobileNetV2 con transfer learning.
    """
    try:
        logger.info(f"🚀 Iniciando entrenamiento CV: {request.epochs} épocas, {request.num_samples} muestras")
        
        result = vision_model.train(
            epochs=request.epochs,
            batch_size=request.batch_size
        )
        
        return {
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en entrenamiento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classes")
async def get_classes():
    """Obtener las clases de detección disponibles."""
    return {
        "classes": OCCUPANCY_CLASSES,
        "descriptions": {
            "VACIO": "0-10% ocupación - Vehículo prácticamente vacío",
            "BAJO": "10-30% ocupación - Pocos pasajeros",
            "MEDIO": "30-60% ocupación - Ocupación moderada",
            "ALTO": "60-80% ocupación - Alta demanda",
            "LLENO": "80-95% ocupación - Vehículo casi lleno",
            "SOBRECARGADO": "95%+ ocupación - Excede capacidad, personas de pie"
        },
        "thresholds": {
            "normal": "≤ 80%",
            "warning": "80-95%",
            "critical": "> 95%"
        }
    }


@router.get("/dashboard-stats")
async def get_dashboard_stats():
    """
    Estadísticas del sistema de visión artificial para el dashboard.
    
    Genera estadísticas simuladas de múltiples vehículos
    monitoreados en tiempo real.
    """
    # Simular monitoreo de 20 vehículos
    vehicles_data = []
    for v_id in range(1, 21):
        level = np.random.choices(
            range(6),
            weights=[0.05, 0.15, 0.30, 0.25, 0.15, 0.10]
        )[0]
        
        people_ranges = [(0,4), (4,12), (12,24), (24,32), (32,38), (38,50)]
        low, high = people_ranges[level]
        people = np.random.randint(low, high + 1)
        capacity = 40
        
        vehicles_data.append({
            "vehiculo_id": v_id,
            "placa": f"SCZ-{v_id:03d}",
            "nivel": OCCUPANCY_CLASSES[level],
            "personas": int(people),
            "capacidad": capacity,
            "porcentaje": round(float(min(1.0, people / capacity)), 4),
        })
    
    # Resumen
    total_people = sum(v["personas"] for v in vehicles_data)
    avg_occ = np.mean([v["porcentaje"] for v in vehicles_data])
    
    level_counts = {}
    for cls in OCCUPANCY_CLASSES:
        level_counts[cls] = len([v for v in vehicles_data if v["nivel"] == cls])
    
    return {
        "total_vehicles_monitored": len(vehicles_data),
        "total_passengers_detected": int(total_people),
        "average_occupancy": round(float(avg_occ), 4),
        "distribution": level_counts,
        "critical_alerts": len([v for v in vehicles_data if v["nivel"] in ["LLENO", "SOBRECARGADO"]]),
        "vehicles": vehicles_data,
        "model_info": {
            "architecture": "MobileNetV2 (TensorFlow)",
            "status": "active" if vision_model.model is not None else "heuristic_fallback",
            "is_trained": vision_model.is_trained,
        },
        "timestamp": datetime.now().isoformat()
    }
