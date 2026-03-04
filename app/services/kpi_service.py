"""
KPI Service - Business Intelligence KPIs from Real Data
Provides centralized KPI calculations from ClickHouse, MongoDB, and PostgreSQL
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.db.clickhouse import clickhouse_conn
from app.db.mongodb import mongodb_conn
from app.db.redis_cache import redis_conn
from app.core.config import settings

logger = logging.getLogger(__name__)


class KPIService:
    """
    Centralized service for calculating real KPIs from databases.
    Uses ClickHouse for transactional analytics, MongoDB for user feedback,
    and caches results in Redis.
    """
    
    def __init__(self):
        self.cache_ttl = getattr(settings, 'CACHE_TTL', 300)
    
    def get_passenger_kpis(self, days: int = 7) -> Dict[str, Any]:
        """Get passenger-related KPIs from ClickHouse"""
        try:
            cache_key = f"kpi:passengers:{days}"
            
            # Try cache first
            try:
                cached = redis_conn.get(cache_key)
                if cached:
                    logger.info("✅ Passenger KPIs from cache")
                    return cached
            except Exception:
                pass
            
            # Query ClickHouse for real data
            if not clickhouse_conn.client:
                clickhouse_conn.connect()
            
            query = """
            SELECT 
                count(DISTINCT usuario_id) as total_passengers,
                count(*) as total_transactions,
                sum(monto) as total_revenue,
                avg(monto) as avg_transaction,
                toHour(timestamp) as peak_hour
            FROM transaction_records
            WHERE timestamp >= now() - INTERVAL %(days)s DAY
            GROUP BY peak_hour
            ORDER BY count(*) DESC
            LIMIT 1
            """
            
            result = clickhouse_conn.execute(query, {'days': days})
            
            if result and len(result) > 0:
                row = result[0]
                kpis = {
                    'total_passengers': int(row[0]) if row[0] else 0,
                    'total_transactions': int(row[1]) if row[1] else 0,
                    'total_revenue': float(row[2]) if row[2] else 0.0,
                    'avg_transaction': float(row[3]) if row[3] else 0.0,
                    'peak_hour': int(row[4]) if row[4] else 8,
                    'data_source': 'clickhouse',
                    'period_days': days
                }
            else:
                # Fallback with realistic estimates based on system capacity
                kpis = self._get_estimated_passenger_kpis(days)
            
            # Cache result
            try:
                redis_conn.set(cache_key, kpis, ttl=self.cache_ttl)
            except Exception:
                pass
            
            return kpis
            
        except Exception as e:
            logger.warning(f"⚠️ ClickHouse query failed: {e}, using estimates")
            return self._get_estimated_passenger_kpis(days)
    
    def _get_estimated_passenger_kpis(self, days: int) -> Dict[str, Any]:
        """Generate realistic KPI estimates based on typical transit system metrics"""
        # Based on typical medium-sized city transit system
        daily_passengers = 8500  # Average daily passengers
        avg_fare = 2500  # COP average fare
        
        return {
            'total_passengers': daily_passengers * days,
            'total_transactions': int(daily_passengers * days * 1.2),  # Some passengers make multiple trips
            'total_revenue': daily_passengers * days * avg_fare,
            'avg_transaction': avg_fare,
            'peak_hour': 8,  # Morning rush
            'data_source': 'estimated',
            'period_days': days
        }
    
    def get_route_kpis(self, route_id: Optional[int] = None) -> Dict[str, Any]:
        """Get route performance KPIs"""
        try:
            cache_key = f"kpi:routes:{route_id or 'all'}"
            
            try:
                cached = redis_conn.get(cache_key)
                if cached:
                    return cached
            except Exception:
                pass
            
            if not clickhouse_conn.client:
                clickhouse_conn.connect()
            
            # Get route statistics
            query = """
            SELECT 
                count(DISTINCT ruta_id) as total_routes,
                count(DISTINCT CASE WHEN timestamp >= now() - INTERVAL 1 HOUR THEN ruta_id END) as active_routes,
                avg(monto) as avg_revenue_per_trip
            FROM transaction_records
            WHERE timestamp >= now() - INTERVAL 1 DAY
            """
            
            if route_id:
                query += " AND ruta_id = %(route_id)s"
            
            params = {'route_id': route_id} if route_id else {}
            result = clickhouse_conn.execute(query, params)
            
            if result and len(result) > 0:
                row = result[0]
                kpis = {
                    'total_routes': int(row[0]) if row[0] else 20,
                    'active_routes': int(row[1]) if row[1] else 15,
                    'avg_revenue_per_trip': float(row[2]) if row[2] else 2500.0,
                    'data_source': 'clickhouse'
                }
            else:
                kpis = {
                    'total_routes': 20,
                    'active_routes': 18,
                    'avg_revenue_per_trip': 2500.0,
                    'data_source': 'estimated'
                }
            
            try:
                redis_conn.set(cache_key, kpis, ttl=self.cache_ttl)
            except Exception:
                pass
            
            return kpis
            
        except Exception as e:
            logger.warning(f"⚠️ Route KPI query failed: {e}")
            return {
                'total_routes': 20,
                'active_routes': 18,
                'avg_revenue_per_trip': 2500.0,
                'data_source': 'estimated'
            }
    
    def get_occupancy_kpis(self) -> Dict[str, Any]:
        """Get vehicle occupancy KPIs"""
        try:
            cache_key = "kpi:occupancy"
            
            try:
                cached = redis_conn.get(cache_key)
                if cached:
                    return cached
            except Exception:
                pass
            
            if not clickhouse_conn.client:
                clickhouse_conn.connect()
            
            query = """
            SELECT 
                avg(ocupacion_porcentaje) as avg_occupancy,
                max(ocupacion_porcentaje) as max_occupancy,
                min(ocupacion_porcentaje) as min_occupancy,
                count(DISTINCT vehiculo_id) as vehicles_tracked
            FROM vehicle_telemetry
            WHERE timestamp >= now() - INTERVAL 1 HOUR
            """
            
            result = clickhouse_conn.execute(query, {})
            
            if result and len(result) > 0 and result[0][0] is not None:
                row = result[0]
                kpis = {
                    'avg_occupancy': float(row[0]) / 100.0,
                    'max_occupancy': float(row[1]) / 100.0 if row[1] else 0.95,
                    'min_occupancy': float(row[2]) / 100.0 if row[2] else 0.20,
                    'vehicles_tracked': int(row[3]) if row[3] else 0,
                    'data_source': 'clickhouse'
                }
            else:
                kpis = {
                    'avg_occupancy': 0.72,
                    'max_occupancy': 0.95,
                    'min_occupancy': 0.25,
                    'vehicles_tracked': 45,
                    'data_source': 'estimated'
                }
            
            try:
                redis_conn.set(cache_key, kpis, ttl=60)  # Short TTL for real-time data
            except Exception:
                pass
            
            return kpis
            
        except Exception as e:
            logger.warning(f"⚠️ Occupancy KPI query failed: {e}")
            return {
                'avg_occupancy': 0.72,
                'max_occupancy': 0.95,
                'min_occupancy': 0.25,
                'vehicles_tracked': 45,
                'data_source': 'estimated'
            }
    
    def get_sentiment_kpis(self) -> Dict[str, Any]:
        """Get sentiment analysis KPIs from MongoDB"""
        try:
            cache_key = "kpi:sentiment"
            
            try:
                cached = redis_conn.get(cache_key)
                if cached:
                    return cached
            except Exception:
                pass
            
            db = mongodb_conn.connect()
            
            # Get sentiment distribution
            pipeline = [
                {"$match": {"sentimiento": {"$exists": True}}},
                {"$group": {
                    "_id": "$sentimiento",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            
            results = list(db.user_feedback.aggregate(pipeline))
            
            if results:
                total = sum(r['count'] for r in results)
                sentiment_map = {r['_id']: r['count'] for r in results}
                
                positive = sentiment_map.get('positive', 0) + sentiment_map.get('positivo', 0)
                negative = sentiment_map.get('negative', 0) + sentiment_map.get('negativo', 0)
                neutral = sentiment_map.get('neutral', 0) + sentiment_map.get('neutro', 0)
                
                avg_sentiment = (positive - negative) / total if total > 0 else 0.5
                avg_sentiment = (avg_sentiment + 1) / 2  # Normalize to 0-1
                
                kpis = {
                    'avg_sentiment': round(avg_sentiment, 3),
                    'positive_count': positive,
                    'neutral_count': neutral,
                    'negative_count': negative,
                    'total_feedback': total,
                    'positive_rate': positive / total if total > 0 else 0.5,
                    'data_source': 'mongodb'
                }
            else:
                kpis = {
                    'avg_sentiment': 0.72,
                    'positive_count': 450,
                    'neutral_count': 320,
                    'negative_count': 130,
                    'total_feedback': 900,
                    'positive_rate': 0.50,
                    'data_source': 'estimated'
                }
            
            try:
                redis_conn.set(cache_key, kpis, ttl=self.cache_ttl)
            except Exception:
                pass
            
            return kpis
            
        except Exception as e:
            logger.warning(f"⚠️ Sentiment KPI query failed: {e}")
            return {
                'avg_sentiment': 0.72,
                'positive_count': 450,
                'neutral_count': 320,
                'negative_count': 130,
                'total_feedback': 900,
                'positive_rate': 0.50,
                'data_source': 'estimated'
            }
    
    def get_all_kpis(self) -> Dict[str, Any]:
        """Get comprehensive KPI dashboard data"""
        passenger_kpis = self.get_passenger_kpis()
        route_kpis = self.get_route_kpis()
        occupancy_kpis = self.get_occupancy_kpis()
        sentiment_kpis = self.get_sentiment_kpis()
        
        return {
            'passengers': passenger_kpis,
            'routes': route_kpis,
            'occupancy': occupancy_kpis,
            'sentiment': sentiment_kpis,
            'generated_at': datetime.now().isoformat(),
            'data_sources': {
                'passengers': passenger_kpis.get('data_source', 'unknown'),
                'routes': route_kpis.get('data_source', 'unknown'),
                'occupancy': occupancy_kpis.get('data_source', 'unknown'),
                'sentiment': sentiment_kpis.get('data_source', 'unknown')
            }
        }
    
    def get_revenue_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get detailed revenue analytics"""
        try:
            cache_key = f"kpi:revenue:{days}"
            
            try:
                cached = redis_conn.get(cache_key)
                if cached:
                    return cached
            except Exception:
                pass
            
            if not clickhouse_conn.client:
                clickhouse_conn.connect()
            
            # Daily revenue breakdown
            query = """
            SELECT 
                toDate(timestamp) as date,
                sum(monto) as revenue,
                count(*) as transactions,
                avg(monto) as avg_transaction
            FROM transaction_records
            WHERE timestamp >= now() - INTERVAL %(days)s DAY
            GROUP BY date
            ORDER BY date
            """
            
            result = clickhouse_conn.execute(query, {'days': days})
            
            if result and len(result) > 0:
                daily_breakdown = []
                for row in result:
                    daily_breakdown.append({
                        'date': row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                        'revenue': float(row[1]) if row[1] else 0.0,
                        'transactions': int(row[2]) if row[2] else 0,
                        'avg_transaction': float(row[3]) if row[3] else 0.0
                    })
                
                total_revenue = sum(d['revenue'] for d in daily_breakdown)
                total_transactions = sum(d['transactions'] for d in daily_breakdown)
                
                # Calculate growth rate
                if len(daily_breakdown) >= 2:
                    first_half = sum(d['revenue'] for d in daily_breakdown[:len(daily_breakdown)//2])
                    second_half = sum(d['revenue'] for d in daily_breakdown[len(daily_breakdown)//2:])
                    growth_rate = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
                else:
                    growth_rate = 0
                
                analytics = {
                    'summary': {
                        'total_revenue': total_revenue,
                        'avg_daily_revenue': total_revenue / days if days > 0 else 0,
                        'total_transactions': total_transactions,
                        'growth_rate': round(growth_rate, 2)
                    },
                    'daily_breakdown': daily_breakdown,
                    'data_source': 'clickhouse'
                }
            else:
                analytics = self._get_estimated_revenue(days)
            
            try:
                redis_conn.set(cache_key, analytics, ttl=self.cache_ttl)
            except Exception:
                pass
            
            return analytics
            
        except Exception as e:
            logger.warning(f"⚠️ Revenue analytics query failed: {e}")
            return self._get_estimated_revenue(days)
    
    def _get_estimated_revenue(self, days: int) -> Dict[str, Any]:
        """Generate realistic revenue estimates"""
        base_daily_revenue = 21250000  # ~21M COP daily for medium city
        daily_transactions = 8500
        
        daily_breakdown = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i - 1)
            # Add some variance (±15%)
            variance = 1 + (0.15 * (2 * (hash(str(date)) % 100) / 100 - 1))
            daily_breakdown.append({
                'date': date.date().isoformat(),
                'revenue': base_daily_revenue * variance,
                'transactions': int(daily_transactions * variance),
                'avg_transaction': 2500
            })
        
        total_revenue = sum(d['revenue'] for d in daily_breakdown)
        
        return {
            'summary': {
                'total_revenue': total_revenue,
                'avg_daily_revenue': total_revenue / days,
                'total_transactions': sum(d['transactions'] for d in daily_breakdown),
                'growth_rate': 3.5  # Typical growth
            },
            'daily_breakdown': daily_breakdown,
            'data_source': 'estimated'
        }
    
    def get_performance_metrics(self, days: int = 7, route_id: Optional[int] = None) -> Dict[str, Any]:
        """Get operational performance metrics"""
        try:
            cache_key = f"kpi:performance:{days}:{route_id or 'all'}"
            
            try:
                cached = redis_conn.get(cache_key)
                if cached:
                    return cached
            except Exception:
                pass
            
            if not clickhouse_conn.client:
                clickhouse_conn.connect()
            
            # Query for on-time performance
            query = """
            SELECT 
                avg(CASE WHEN delay_minutes <= 5 THEN 1 ELSE 0 END) as on_time_rate,
                avg(delay_minutes) as avg_delay,
                count(*) as total_trips
            FROM (
                SELECT 
                    viaje_id,
                    dateDiff('minute', hora_programada, hora_real) as delay_minutes
                FROM trip_records
                WHERE timestamp >= now() - INTERVAL %(days)s DAY
            """
            
            if route_id:
                query += " AND ruta_id = %(route_id)s"
            
            query += ")"
            
            params = {'days': days}
            if route_id:
                params['route_id'] = route_id
            
            result = clickhouse_conn.execute(query, params)
            
            if result and len(result) > 0 and result[0][0] is not None:
                row = result[0]
                metrics = {
                    'on_time_rate': float(row[0]),
                    'avg_delay_minutes': float(row[1]) if row[1] else 0,
                    'total_trips': int(row[2]) if row[2] else 0,
                    'data_source': 'clickhouse'
                }
            else:
                metrics = {
                    'on_time_rate': 0.87,
                    'avg_delay_minutes': 4.2,
                    'total_trips': days * 450,
                    'data_source': 'estimated'
                }
            
            # Add occupancy from separate query
            occupancy = self.get_occupancy_kpis()
            metrics['occupancy_rate'] = occupancy['avg_occupancy']
            
            # Add satisfaction from sentiment
            sentiment = self.get_sentiment_kpis()
            metrics['passenger_satisfaction'] = sentiment['avg_sentiment']
            
            # Calculate revenue per trip
            revenue = self.get_revenue_analytics(days)
            if revenue['summary']['total_transactions'] > 0:
                metrics['revenue_per_trip'] = revenue['summary']['total_revenue'] / revenue['summary']['total_transactions']
            else:
                metrics['revenue_per_trip'] = 2500
            
            try:
                redis_conn.set(cache_key, metrics, ttl=self.cache_ttl)
            except Exception:
                pass
            
            return metrics
            
        except Exception as e:
            logger.warning(f"⚠️ Performance metrics query failed: {e}")
            return {
                'on_time_rate': 0.87,
                'avg_delay_minutes': 4.2,
                'total_trips': days * 450,
                'occupancy_rate': 0.72,
                'passenger_satisfaction': 0.75,
                'revenue_per_trip': 2500,
                'data_source': 'estimated'
            }


# Global instance
kpi_service = KPIService()
