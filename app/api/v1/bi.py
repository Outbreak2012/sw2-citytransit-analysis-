"""
Business Intelligence API Endpoints
====================================
Endpoints completos para BI Dashboard en Python:
- KPIs en tiempo real
- Análisis de rentabilidad
- Segmentación de mercado
- Forecast financiero
- Exportación de datasets
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_bi_engine():
    """Obtener instancia del motor de BI."""
    from app.services.bi_service import bi_engine
    return bi_engine


# === KPIs Dashboard ===

@router.get("/bi/dashboard")
async def bi_dashboard():
    """
    Dashboard completo de Business Intelligence.
    Retorna todos los KPIs del sistema organizados por categoría.
    """
    try:
        engine = get_bi_engine()
        kpis = engine.calculate_all_kpis()
        
        return {
            "status": "success",
            "dashboard": "Business Intelligence - PayTransit",
            "data": kpis,
            "datasets_info": engine.get_dataset_info(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en BI dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bi/kpis")
async def get_kpis(
    category: Optional[str] = Query(None, description="Categoría: operational, financial, users, satisfaction, routes, ml_models")
):
    """
    Obtener KPIs por categoría o todos.
    
    Categorías disponibles:
    - operational: Transacciones, vehículos, ocupación
    - financial: Ingresos, utilidad, ROI, ticket promedio
    - users: Usuarios activos, churn, segmentación
    - satisfaction: NPS, sentimiento, categorías
    - routes: Top rutas, tipo pago, hora pico
    - ml_models: Estado modelos ML activos
    """
    try:
        engine = get_bi_engine()
        all_kpis = engine.calculate_all_kpis()
        
        if category:
            if category not in all_kpis:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Categoría '{category}' no válida. Opciones: {list(all_kpis.keys())}"
                )
            return {
                "status": "success",
                "category": category,
                "kpis": all_kpis[category],
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "success",
            "kpis": all_kpis,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Análisis ===

@router.get("/bi/profitability")
async def analyze_profitability():
    """
    Análisis de rentabilidad por ruta.
    Calcula ingresos, costos, utilidad y margen de cada ruta.
    """
    try:
        engine = get_bi_engine()
        result = engine.analyze_profitability()
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en análisis de rentabilidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bi/segmentation")
async def analyze_segmentation():
    """
    Análisis de segmentación de mercado por valor de usuario.
    Segmenta usuarios en: Bajo valor, Medio-bajo, Medio-alto, Alto valor.
    """
    try:
        engine = get_bi_engine()
        result = engine.analyze_user_segments()
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en segmentación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bi/forecast")
async def forecast_revenue(
    months: int = Query(3, ge=1, le=12, description="Meses a proyectar (1-12)")
):
    """
    Proyección de ingresos futuros.
    Utiliza tendencia lineal sobre datos históricos.
    """
    try:
        engine = get_bi_engine()
        result = engine.forecast_revenue(months_ahead=months)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Datasets ===

@router.get("/bi/datasets")
async def list_datasets():
    """
    Listar todos los datasets disponibles con metadatos.
    """
    try:
        engine = get_bi_engine()
        info = engine.get_dataset_info()
        
        return {
            "status": "success",
            "data": info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listando datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bi/datasets/{dataset_name}")
async def get_dataset(
    dataset_name: str,
    format: str = Query("summary", description="Formato: json, csv, summary")
):
    """
    Obtener o exportar un dataset específico.
    
    Datasets disponibles:
    - transactions: 50K transacciones de 6 meses
    - users: 2K usuarios con métricas
    - routes: 12 rutas de Santa Cruz
    - vehicles: 55 vehículos
    - feedbacks: 5K feedbacks de 3 meses
    - financial: 12 meses de datos financieros
    """
    try:
        engine = get_bi_engine()
        result = engine.export_dataset(dataset_name, format=format)
        
        return {
            "status": "success",
            "dataset": dataset_name,
            "format": format,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error exportando dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Resumen Ejecutivo ===

@router.get("/bi/executive-summary")
async def executive_summary():
    """
    Resumen ejecutivo completo BI.
    Combina KPIs clave, insights y recomendaciones automáticas.
    """
    try:
        engine = get_bi_engine()
        kpis = engine.calculate_all_kpis()
        profitability = engine.analyze_profitability()
        segments = engine.analyze_user_segments()
        forecast = engine.forecast_revenue(3)
        
        # Generar insights automáticos
        insights = []
        
        # Insight financiero
        fin = kpis['financial']
        if fin['crecimiento_mensual'] > 0:
            insights.append({
                "tipo": "positivo",
                "area": "Financiero",
                "mensaje": f"Crecimiento mensual de {fin['crecimiento_mensual']}%. Tendencia positiva sostenida.",
            })
        else:
            insights.append({
                "tipo": "alerta",
                "area": "Financiero",
                "mensaje": f"Decrecimiento de {abs(fin['crecimiento_mensual'])}%. Requiere atención inmediata.",
            })
        
        # Insight usuarios
        usr = kpis['users']
        if usr['usuarios_alto_riesgo'] > 100:
            insights.append({
                "tipo": "alerta",
                "area": "Retención",
                "mensaje": f"{usr['usuarios_alto_riesgo']} usuarios con alto riesgo de churn. Implementar campaña de retención.",
            })
        
        # Insight satisfacción
        sat = kpis['satisfaction']
        if sat['porcentaje_positivo'] > 50:
            insights.append({
                "tipo": "positivo",
                "area": "Satisfacción",
                "mensaje": f"{sat['porcentaje_positivo']}% de feedbacks positivos. Score promedio: {sat['score_promedio']}/5.",
            })
        
        # Insight ocupación
        ops = kpis['operational']
        if ops['ocupacion_hora_pico'] > 80:
            insights.append({
                "tipo": "alerta",
                "area": "Operaciones",
                "mensaje": f"Ocupación en hora pico: {ops['ocupacion_hora_pico']}%. Considerar más unidades.",
            })
        
        # Recomendaciones
        recommendations = [
            {
                "prioridad": "alta",
                "acción": "Optimizar rutas con mayor demanda para reducir tiempos de espera",
                "impacto_estimado": "↑15% satisfacción usuarios"
            },
            {
                "prioridad": "alta", 
                "acción": "Implementar precios dinámicos en hora pico para balancear demanda",
                "impacto_estimado": "↑8% ingresos"
            },
            {
                "prioridad": "media",
                "acción": "Campaña de retención para usuarios con churn_risk > 0.7",
                "impacto_estimado": "↓20% churn rate"
            },
            {
                "prioridad": "media",
                "acción": "Expandir adopción de pago NFC para reducir tiempos de abordaje",
                "impacto_estimado": "↑10% eficiencia operativa"
            },
        ]
        
        return {
            "status": "success",
            "resumen_ejecutivo": {
                "periodo": "Últimos 6 meses",
                "generado": datetime.now().isoformat(),
                "kpis_principales": {
                    "ingresos_mensuales": fin['ingresos_mes_actual'],
                    "margen_neto": fin['margen_neto'],
                    "usuarios_activos": usr['usuarios_activos_30d'],
                    "satisfaccion": sat['score_promedio'],
                    "ocupacion_promedio": ops['ocupacion_promedio'],
                    "vehiculos_activos": ops['vehiculos_activos'],
                    "rutas_activas": ops['rutas_activas'],
                    "modelos_ml": kpis['ml_models']['modelos_activos'],
                },
                "insights": insights,
                "rentabilidad": {
                    "ruta_top": profitability['ruta_más_rentable'],
                    "margen_promedio": profitability['margen_promedio'],
                },
                "segmentacion": segments,
                "proyeccion": forecast,
                "recomendaciones": recommendations,
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generando resumen ejecutivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
