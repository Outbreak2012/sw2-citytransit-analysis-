from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from app.models.schemas import KPIResponse, ReportRequest, ReportResponse
from app.core.security import get_current_user
from app.services.kpi_service import kpi_service
from app.services.report_service import report_service
import logging
import uuid
from app.core.config import settings
from app.db.redis_cache import redis_conn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports & KPIs"])


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    current_user: dict = Depends(get_current_user)
):
    """Get current KPIs dashboard"""
    try:
        logger.info("Getting KPIs...")
        cache_key = "kpis_v1"

        # Try to get from cache (fail gracefully if Redis not available)
        try:
            cached = redis_conn.get(cache_key)
            if cached:
                logger.info("✅ KPIs returned from cache")
                return KPIResponse(**cached)
        except Exception:
            logger.warning("⚠️ Redis not available, continuing without cache")

        # Get real KPI data from services
        all_kpis = kpi_service.get_all_kpis()
        
        kpi = KPIResponse(
            total_passengers=all_kpis['passengers']['total_passengers'],
            total_revenue=all_kpis['passengers']['total_revenue'],
            avg_occupancy=all_kpis['occupancy']['avg_occupancy'],
            routes_active=all_kpis['routes']['active_routes'],
            peak_hour=all_kpis['passengers']['peak_hour'],
            sentiment_avg=all_kpis['sentiment']['avg_sentiment'],
            generated_at=datetime.now()
        )

        # Cache result (store ISO string for datetime)
        try:
            payload = kpi.dict()
            if isinstance(payload.get('generated_at'), datetime):
                payload['generated_at'] = payload['generated_at'].isoformat()
            redis_conn.set(cache_key, payload, ttl=getattr(settings, 'CACHE_TTL', 300))
            logger.info("✅ KPIs cached")
        except Exception:
            logger.warning("⚠️ Could not write KPIs to Redis cache")

        return kpi
        
    except Exception as e:
        logger.error(f"Error getting KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive dashboard data"""
    try:
        logger.info(f"Getting {period} dashboard...")

        cache_key = f"dashboard:{period}"

        try:
            cached = redis_conn.get(cache_key)
            if cached:
                logger.info("✅ Dashboard returned from cache")
                return cached
        except Exception:
            logger.warning("⚠️ Redis not available, continuing without cache")

        # Calculate days based on period
        days = {'daily': 1, 'weekly': 7, 'monthly': 30}.get(period, 7)
        
        # Get real data from services
        all_kpis = kpi_service.get_all_kpis()
        revenue_data = kpi_service.get_revenue_analytics(days)
        performance = kpi_service.get_performance_metrics(days)
        
        # Get top routes from report service
        route_report = report_service.generate_route_performance_report(days=days)
        top_routes = route_report['routes'][:5] if route_report['routes'] else []
        
        dashboard = {
            "period": period,
            "metrics": {
                "total_passengers": all_kpis['passengers']['total_passengers'],
                "total_revenue": revenue_data['summary']['total_revenue'],
                "total_trips": revenue_data['summary']['total_transactions'],
                "avg_occupancy": all_kpis['occupancy']['avg_occupancy'],
                "on_time_performance": performance['on_time_rate']
            },
            "routes": {
                "total": all_kpis['routes']['total_routes'],
                "active": all_kpis['routes']['active_routes'],
                "peak_routes": [
                    {"route_id": r['route_id'], "name": f"Ruta {r['route_id']}", "passengers": r['unique_passengers']}
                    for r in top_routes
                ]
            },
            "trends": {
                "passenger_growth": revenue_data['summary']['growth_rate'],
                "revenue_growth": revenue_data['summary']['growth_rate'],
                "satisfaction_score": all_kpis['sentiment']['avg_sentiment']
            },
            "alerts": _generate_alerts(all_kpis, performance),
            "data_sources": all_kpis['data_sources'],
            "generated_at": datetime.now()
        }
        
        # Try to cache the generated dashboard (do not fail if Redis missing)
        try:
            to_cache = dict(dashboard)
            if isinstance(to_cache.get('generated_at'), datetime):
                to_cache['generated_at'] = to_cache['generated_at'].isoformat()
            redis_conn.set(cache_key, to_cache, ttl=getattr(settings, 'CACHE_TTL', 300))
            logger.info("✅ Dashboard cached")
        except Exception:
            logger.warning("⚠️ Could not write dashboard to Redis cache")

        return dashboard

    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_alerts(kpis: dict, performance: dict) -> list:
    """Generate system alerts based on KPIs"""
    alerts = []
    
    # Check occupancy
    if kpis['occupancy']['avg_occupancy'] > 0.85:
        alerts.append({
            "type": "warning",
            "message": "Alta ocupación detectada en múltiples rutas",
            "timestamp": datetime.now().isoformat()
        })
    
    # Check on-time performance
    if performance.get('on_time_rate', 1) < 0.80:
        alerts.append({
            "type": "warning",
            "message": "Puntualidad por debajo del objetivo (80%)",
            "timestamp": datetime.now().isoformat()
        })
    
    # Check sentiment
    if kpis['sentiment']['avg_sentiment'] < 0.60:
        alerts.append({
            "type": "alert",
            "message": "Satisfacción del cliente requiere atención",
            "timestamp": datetime.now().isoformat()
        })
    
    # Always add info alert
    if not alerts:
        alerts.append({
            "type": "info",
            "message": "Sistema operando con normalidad",
            "timestamp": datetime.now().isoformat()
        })
    
    return alerts


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate custom report"""
    try:
        logger.info(f"Generating {request.report_type} report...")
        
        report_id = str(uuid.uuid4())
        
        # Simulate report generation
        return ReportResponse(
            report_id=report_id,
            report_type=request.report_type,
            status="completed",
            download_url=f"/api/v1/reports/download/{report_id}",
            generated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{report_id}")
async def download_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download generated report"""
    try:
        logger.info(f"Downloading report {report_id}...")
        
        # Report data (in production, fetch from storage)
        import hashlib
        # Generate consistent record count based on report_id
        records = 100 + (int(hashlib.md5(report_id.encode()).hexdigest()[:8], 16) % 900)
        
        return {
            "report_id": report_id,
            "status": "ready",
            "data": {
                "summary": "Reporte generado exitosamente",
                "records": records,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics(
    route_id: int = Query(None, description="Filter by route"),
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get performance metrics"""
    try:
        logger.info(f"Getting performance metrics for {days} days...")
        
        # Get real performance metrics from KPI service
        metrics = kpi_service.get_performance_metrics(days=days, route_id=route_id)
        
        result = {
            "on_time_rate": metrics['on_time_rate'],
            "avg_delay_minutes": metrics['avg_delay_minutes'],
            "passenger_satisfaction": metrics['passenger_satisfaction'],
            "revenue_per_trip": metrics['revenue_per_trip'],
            "occupancy_rate": metrics['occupancy_rate'],
            "period": {
                "days": days,
                "from": (datetime.now() - timedelta(days=days)).isoformat(),
                "to": datetime.now().isoformat()
            },
            "data_source": metrics.get('data_source', 'unknown'),
            "generated_at": datetime.now()
        }
        
        if route_id:
            result["route_id"] = route_id
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue")
async def get_revenue_analysis(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get revenue analysis"""
    try:
        logger.info(f"Getting revenue analysis for {days} days...")
        
        # Get real revenue data from KPI service
        revenue_data = kpi_service.get_revenue_analytics(days)
        
        return {
            "summary": revenue_data['summary'],
            "daily_breakdown": revenue_data['daily_breakdown'],
            "period": {
                "days": days,
                "from": (datetime.now() - timedelta(days=days)).isoformat(),
                "to": datetime.now().isoformat()
            },
            "data_source": revenue_data.get('data_source', 'unknown'),
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting revenue analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executive-summary")
async def get_executive_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get executive summary with key metrics and recommendations"""
    try:
        logger.info(f"Generating executive summary for {days} days...")
        
        summary = report_service.generate_executive_summary(days=days)
        return summary
        
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/route-performance")
async def get_route_performance_report(
    route_id: int = Query(None, description="Specific route ID"),
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed route performance report"""
    try:
        logger.info(f"Generating route performance report...")
        
        report = report_service.generate_route_performance_report(route_id=route_id, days=days)
        return report
        
    except Exception as e:
        logger.error(f"Error generating route report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demand-forecast")
async def get_demand_forecast(
    route_id: int = Query(None, description="Specific route ID"),
    days_ahead: int = Query(7, ge=1, le=30, description="Days to forecast"),
    current_user: dict = Depends(get_current_user)
):
    """Get demand forecast using LSTM model"""
    try:
        logger.info(f"Generating demand forecast for {days_ahead} days...")
        
        forecast = report_service.generate_demand_forecast_report(
            route_id=route_id, 
            days_ahead=days_ahead
        )
        return forecast
        
    except Exception as e:
        logger.error(f"Error generating demand forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment-report")
async def get_sentiment_report(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed sentiment analysis report"""
    try:
        logger.info(f"Generating sentiment report for {days} days...")
        
        report = report_service.generate_sentiment_report(days=days)
        return report
        
    except Exception as e:
        logger.error(f"Error generating sentiment report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-kpis")
async def get_all_kpis(
    current_user: dict = Depends(get_current_user)
):
    """Get all KPIs from all data sources"""
    try:
        logger.info("Getting all KPIs...")
        
        all_kpis = kpi_service.get_all_kpis()
        return all_kpis
        
    except Exception as e:
        logger.error(f"Error getting all KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
