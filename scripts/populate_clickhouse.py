"""
Script para poblar ClickHouse con datos sintéticos realistas
Genera transacciones históricas de los últimos 6 meses
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from clickhouse_driver import Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClickHouseDataGenerator:
    """Generador de datos sintéticos para ClickHouse"""
    
    def __init__(self, host='localhost', port=9000):
        # Conectar sin especificar database para poder crearla
        self.client = Client(
            host=host, 
            port=port,
            user='default',
            password='redfire007'
        )
        
    def create_tables(self):
        """Crear tablas en ClickHouse"""
        logger.info("📊 Creando base de datos y tablas en ClickHouse...")
        
        # Crear base de datos
        self.client.execute("CREATE DATABASE IF NOT EXISTS citytransit")
        
        # Tabla de transacciones
        self.client.execute("""
            CREATE TABLE IF NOT EXISTS citytransit.transaction_records (
                transaction_id UInt64,
                timestamp DateTime,
                route_id UInt32,
                vehicle_id UInt32,
                passenger_count UInt16,
                fare_amount Float32,
                hour UInt8,
                day_of_week UInt8,
                month UInt8,
                is_weekend UInt8,
                is_holiday UInt8,
                temperature Float32,
                precipitation Float32,
                events_count UInt8,
                demand Float32,
                occupancy_rate Float32
            ) ENGINE = MergeTree()
            ORDER BY (route_id, timestamp)
        """)
        
        logger.info("✅ Tablas creadas exitosamente")
    
    def generate_weather_data(self, timestamp):
        """Generar datos de clima realistas"""
        # Temperatura base según mes (Colombia)
        month = timestamp.month
        base_temps = {
            1: 18, 2: 19, 3: 20, 4: 20, 5: 19, 6: 18,
            7: 18, 8: 18, 9: 19, 10: 19, 11: 19, 12: 18
        }
        
        hour = timestamp.hour
        # Variación diurna
        hour_adjustment = -3 if hour < 6 else (2 if 12 <= hour <= 15 else 0)
        
        temperature = base_temps[month] + hour_adjustment + np.random.normal(0, 1.5)
        
        # Precipitación (mayor en abril-mayo, octubre-noviembre)
        rain_months = [4, 5, 10, 11]
        rain_prob = 0.3 if month in rain_months else 0.1
        precipitation = np.random.exponential(3) if np.random.random() < rain_prob else 0
        
        return temperature, precipitation
    
    def is_holiday(self, date):
        """Determinar si es festivo (Colombia 2024-2025)"""
        holidays = [
            (1, 1), (1, 8), (3, 25), (3, 28), (3, 29),  # Enero-Marzo
            (5, 1), (5, 13), (6, 3), (6, 10), (6, 24),  # Mayo-Junio
            (7, 1), (7, 20), (8, 7), (8, 19),           # Julio-Agosto
            (10, 14), (11, 4), (11, 11), (12, 8), (12, 25)  # Oct-Dic
        ]
        return 1 if (date.month, date.day) in holidays else 0
    
    def get_events_count(self, date, hour):
        """Eventos especiales (conciertos, partidos, etc.)"""
        # Más eventos viernes-domingo en la noche
        if date.weekday() >= 4 and 18 <= hour <= 22:
            return np.random.poisson(2)
        elif date.weekday() == 5:  # Sábado
            return np.random.poisson(1.5)
        else:
            return np.random.poisson(0.3)
    
    def calculate_demand(self, hour, day_of_week, is_weekend, is_holiday, 
                        temperature, precipitation, events_count, route_id):
        """Calcular demanda realista basada en múltiples factores"""
        
        # Base por ruta (algunas rutas son más populares)
        route_popularity = {
            1: 80, 2: 65, 3: 90, 4: 55, 5: 75,
            6: 60, 7: 70, 8: 50, 9: 85, 10: 45
        }
        base_demand = route_popularity.get(route_id, 60)
        
        # Patrón horario (horas pico: 6-8am, 5-7pm)
        hour_factors = {
            0: 0.1, 1: 0.05, 2: 0.05, 3: 0.05, 4: 0.1, 5: 0.3,
            6: 1.8, 7: 2.0, 8: 1.5, 9: 0.8, 10: 0.7, 11: 0.8,
            12: 1.0, 13: 0.9, 14: 0.8, 15: 0.9, 16: 1.2,
            17: 1.8, 18: 2.0, 19: 1.3, 20: 0.8, 21: 0.5,
            22: 0.3, 23: 0.2
        }
        hour_factor = hour_factors[hour]
        
        # Factor día de semana
        weekday_factor = 0.7 if is_weekend else 1.0
        
        # Factor festivo (menos demanda laboral, más recreacional)
        holiday_factor = 0.6 if is_holiday else 1.0
        
        # Factor clima (lluvia reduce demanda)
        weather_factor = max(0.5, 1.0 - (precipitation * 0.1))
        
        # Factor eventos (aumenta demanda)
        events_factor = 1.0 + (events_count * 0.15)
        
        # Factor temperatura (temperaturas extremas reducen demanda)
        temp_factor = 1.0
        if temperature < 12:
            temp_factor = 0.85
        elif temperature > 28:
            temp_factor = 0.9
        
        # Calcular demanda
        demand = (base_demand * hour_factor * weekday_factor * 
                 holiday_factor * weather_factor * events_factor * temp_factor)
        
        # Añadir ruido aleatorio
        demand = demand * (1 + np.random.normal(0, 0.15))
        
        return max(0, demand)
    
    def generate_historical_data(self, months=6, routes=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]):
        """Generar datos históricos"""
        logger.info(f"🔄 Generando {months} meses de datos históricos...")
        
        # Rango de fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        records = []
        transaction_id = 1
        
        # Iterar por cada hora
        current_date = start_date
        while current_date <= end_date:
            hour = current_date.hour
            day_of_week = current_date.weekday()
            month = current_date.month
            is_weekend = 1 if day_of_week >= 5 else 0
            is_holiday_flag = self.is_holiday(current_date)
            
            # Generar clima
            temperature, precipitation = self.generate_weather_data(current_date)
            events_count = self.get_events_count(current_date.date(), hour)
            
            # Generar transacciones para cada ruta
            for route_id in routes:
                # Calcular demanda
                demand = self.calculate_demand(
                    hour, day_of_week, is_weekend, is_holiday_flag,
                    temperature, precipitation, events_count, route_id
                )
                
                # Número de pasajeros (basado en demanda)
                passenger_count = int(np.random.poisson(demand / 10))
                
                if passenger_count > 0:
                    # Vehicle ID (10 vehículos por ruta)
                    vehicle_id = (route_id * 10) + np.random.randint(1, 11)
                    
                    # Tarifa promedio
                    fare_amount = 2500 + np.random.normal(0, 200)
                    
                    # Tasa de ocupación (0-1)
                    max_capacity = 50
                    occupancy_rate = min(1.0, passenger_count / max_capacity)
                    
                    records.append({
                        'transaction_id': transaction_id,
                        'timestamp': current_date,
                        'route_id': route_id,
                        'vehicle_id': vehicle_id,
                        'passenger_count': passenger_count,
                        'fare_amount': fare_amount,
                        'hour': hour,
                        'day_of_week': day_of_week,
                        'month': month,
                        'is_weekend': is_weekend,
                        'is_holiday': is_holiday_flag,
                        'temperature': temperature,
                        'precipitation': precipitation,
                        'events_count': events_count,
                        'demand': demand,
                        'occupancy_rate': occupancy_rate
                    })
                    
                    transaction_id += 1
            
            # Siguiente hora
            current_date += timedelta(hours=1)
            
            # Log progreso cada semana
            if transaction_id % 1000 == 0:
                logger.info(f"   Generados {transaction_id} registros...")
        
        logger.info(f"✅ Generados {len(records)} registros de transacciones")
        return pd.DataFrame(records)
    
    def insert_data(self, df):
        """Insertar datos en ClickHouse"""
        logger.info("💾 Insertando datos en ClickHouse...")
        
        # Convertir DataFrame a lista de tuplas
        data = [tuple(row) for row in df.values]
        
        # Insertar en batch
        self.client.execute(
            """
            INSERT INTO citytransit.transaction_records VALUES
            """,
            data
        )
        
        logger.info(f"✅ Insertados {len(data)} registros exitosamente")
    
    def verify_data(self):
        """Verificar datos insertados"""
        result = self.client.execute(
            "SELECT COUNT(*) FROM citytransit.transaction_records"
        )
        count = result[0][0]
        logger.info(f"📊 Total de registros en ClickHouse: {count:,}")
        
        # Estadísticas
        stats = self.client.execute("""
            SELECT 
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date,
                AVG(demand) as avg_demand,
                AVG(passenger_count) as avg_passengers,
                AVG(occupancy_rate) as avg_occupancy
            FROM citytransit.transaction_records
        """)
        
        logger.info(f"   Fecha inicio: {stats[0][0]}")
        logger.info(f"   Fecha fin: {stats[0][1]}")
        logger.info(f"   Demanda promedio: {stats[0][2]:.2f}")
        logger.info(f"   Pasajeros promedio: {stats[0][3]:.2f}")
        logger.info(f"   Ocupación promedio: {stats[0][4]:.2%}")


def main():
    """Función principal"""
    logger.info("🚀 Iniciando población de ClickHouse con datos sintéticos")
    
    # Crear generador
    generator = ClickHouseDataGenerator(host='localhost', port=9000)
    
    try:
        # Crear tablas
        generator.create_tables()
        
        # Generar datos (6 meses)
        df = generator.generate_historical_data(months=6)
        
        # Insertar datos
        generator.insert_data(df)
        
        # Verificar
        generator.verify_data()
        
        logger.info("🎉 ¡Proceso completado exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
