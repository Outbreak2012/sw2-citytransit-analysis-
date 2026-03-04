import pandas as pd
import logging
from datetime import datetime, timedelta
from app.db.clickhouse import clickhouse_conn
from app.core.config import settings

logger = logging.getLogger(__name__)


class DemandDataService:
    """Service for fetching demand data from ClickHouse"""
    
    def __init__(self):
        self.client = None
    
    def get_historical_demand(self, route_id: int = None, days: int = 30) -> pd.DataFrame:
        """
        Fetch historical demand data from ClickHouse
        Returns DataFrame with features for LSTM model
        """
        try:
            if not clickhouse_conn.client:
                clickhouse_conn.connect()
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Build query - adapt to your ClickHouse schema
            query = """
            SELECT 
                toDateTime(timestamp) as timestamp,
                toHour(timestamp) as hour,
                toDayOfWeek(timestamp) as day_of_week,
                toMonth(timestamp) as month,
                if(toDayOfWeek(timestamp) >= 6, 1, 0) as is_weekend,
                0 as is_holiday,
                20.0 as temperature,
                0.0 as precipitation,
                0 as events_count,
                count(*) as demand
            FROM transaction_records
            WHERE timestamp >= %(start_date)s 
            AND timestamp <= %(end_date)s
            """
            
            if route_id:
                query += " AND ruta_id = %(route_id)s"
            
            query += """
            GROUP BY timestamp, hour, day_of_week, month, is_weekend, 
                     is_holiday, temperature, precipitation, events_count
            ORDER BY timestamp
            """
            
            params = {
                'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': end_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if route_id:
                params['route_id'] = route_id
            
            # Execute query
            result = clickhouse_conn.execute(query, params)
            
            # Convert to DataFrame
            columns = ['timestamp', 'hour', 'day_of_week', 'month', 'is_weekend',
                      'is_holiday', 'temperature', 'precipitation', 'events_count', 'demand']
            df = pd.DataFrame(result, columns=columns)
            
            if df.empty:
                logger.warning(f"⚠️ No historical data found in ClickHouse for route {route_id}")
                return None
            
            # Add derived features
            df['previous_demand'] = df['demand'].shift(1).fillna(df['demand'].mean())
            df['rolling_mean'] = df['demand'].rolling(window=6).mean().fillna(df['demand'].mean())
            
            logger.info(f"✅ Fetched {len(df)} records from ClickHouse")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching historical demand: {e}")
            return None
    
    def get_realtime_metrics(self, route_id: int = None) -> dict:
        """Get real-time demand metrics"""
        try:
            if not clickhouse_conn.client:
                clickhouse_conn.connect()
            
            query = """
            SELECT 
                count(*) as total_transactions,
                avg(monto) as avg_amount,
                toHour(now()) as current_hour
            FROM transaction_records
            WHERE timestamp >= now() - INTERVAL 1 HOUR
            """
            
            if route_id:
                query += " AND ruta_id = %(route_id)s"
            
            params = {'route_id': route_id} if route_id else {}
            result = clickhouse_conn.execute(query, params)
            
            if result:
                return {
                    'total_transactions': result[0][0],
                    'avg_amount': float(result[0][1]) if result[0][1] else 0.0,
                    'current_hour': result[0][2]
                }
            
            return {'total_transactions': 0, 'avg_amount': 0.0, 'current_hour': datetime.now().hour}
            
        except Exception as e:
            logger.error(f"❌ Error fetching realtime metrics: {e}")
            return {'total_transactions': 0, 'avg_amount': 0.0, 'current_hour': datetime.now().hour}


# Global instance
demand_service = DemandDataService()
