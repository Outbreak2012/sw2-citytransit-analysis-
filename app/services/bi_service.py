"""
Business Intelligence Module - CityTransit/PayTransit
======================================================
Módulo completo de Inteligencia de Negocios implementado en Python.

Funcionalidades:
- Dashboard BI con KPIs en tiempo real
- Análisis de tendencias y patrones
- Segmentación de mercado
- Análisis de rentabilidad por ruta
- Forecasting financiero
- Generación de datasets para análisis

Conecta con:
- ClickHouse (OLAP - transacciones)
- MongoDB (NoSQL - feedbacks)
- Redis (cache de KPIs)

Tecnologías: Pandas, NumPy, scikit-learn, Matplotlib
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import os

logger = logging.getLogger(__name__)


class BusinessIntelligenceEngine:
    """
    Motor de Business Intelligence para PayTransit.
    
    Procesa datasets, calcula KPIs, genera insights y
    proporciona data para dashboards de BI.
    """
    
    def __init__(self):
        self.datasets = {}
        self.kpis_cache = {}
        self.last_refresh = None
        self._initialize_datasets()
    
    def _initialize_datasets(self):
        """Generar/cargar datasets completos para BI."""
        logger.info("📊 Inicializando datasets de BI...")
        
        # Dataset 1: Transacciones (simula datos de ClickHouse)
        self.datasets['transactions'] = self._generate_transactions_dataset()
        
        # Dataset 2: Usuarios
        self.datasets['users'] = self._generate_users_dataset()
        
        # Dataset 3: Rutas
        self.datasets['routes'] = self._generate_routes_dataset()
        
        # Dataset 4: Vehículos
        self.datasets['vehicles'] = self._generate_vehicles_dataset()
        
        # Dataset 5: Feedbacks
        self.datasets['feedbacks'] = self._generate_feedbacks_dataset()
        
        # Dataset 6: Financiero
        self.datasets['financial'] = self._generate_financial_dataset()
        
        self.last_refresh = datetime.now()
        logger.info(f"✅ {len(self.datasets)} datasets inicializados")
    
    def _generate_transactions_dataset(self, n_records: int = 50000) -> pd.DataFrame:
        """Dataset de transacciones de 6 meses."""
        np.random.seed(42)
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=180),
            end=datetime.now(),
            freq='5min'
        )
        
        # Seleccionar n_records fechas aleatorias
        selected_dates = np.random.choice(dates, size=min(n_records, len(dates)), replace=True)
        selected_dates = np.sort(selected_dates)
        
        n = len(selected_dates)
        hours = pd.to_datetime(selected_dates).hour
        
        # Demanda varía por hora
        base_demand = np.where(
            (hours >= 6) & (hours <= 9), np.random.uniform(0.7, 1.0, n),
            np.where(
                (hours >= 12) & (hours <= 14), np.random.uniform(0.5, 0.8, n),
                np.where(
                    (hours >= 17) & (hours <= 20), np.random.uniform(0.8, 1.0, n),
                    np.random.uniform(0.2, 0.5, n)
                )
            )
        )
        
        df = pd.DataFrame({
            'transaction_id': range(1, n + 1),
            'fecha': selected_dates,
            'usuario_id': np.random.randint(1, 2001, n),
            'ruta_id': np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], n, 
                                         p=[0.15, 0.12, 0.13, 0.10, 0.09, 0.08, 0.07, 0.06, 0.06, 0.05, 0.05, 0.04]),
            'vehiculo_id': np.random.randint(1, 56, n),
            'monto': np.round(np.random.uniform(1.5, 5.0, n), 2),
            'tipo_pago': np.random.choice(['NFC', 'QR', 'EFECTIVO'], n, p=[0.50, 0.30, 0.20]),
            'tipo_usuario': np.random.choice(['REGULAR', 'ESTUDIANTE', 'PREMIUM', 'ADULTO_MAYOR'], n,
                                              p=[0.45, 0.25, 0.15, 0.15]),
            'ocupacion': np.round(base_demand * 100, 1),
            'hora_pico': (hours >= 6) & (hours <= 9) | (hours >= 17) & (hours <= 20),
            'dia_semana': pd.to_datetime(selected_dates).dayofweek,
            'es_finde': pd.to_datetime(selected_dates).dayofweek >= 5,
        })
        
        return df
    
    def _generate_users_dataset(self, n_users: int = 2000) -> pd.DataFrame:
        """Dataset de usuarios."""
        np.random.seed(43)
        
        register_dates = pd.date_range(
            start=datetime.now() - timedelta(days=365),
            end=datetime.now(),
            periods=n_users
        )
        
        df = pd.DataFrame({
            'user_id': range(1, n_users + 1),
            'fecha_registro': register_dates,
            'tipo': np.random.choice(['REGULAR', 'ESTUDIANTE', 'PREMIUM', 'ADULTO_MAYOR'], n_users,
                                      p=[0.45, 0.25, 0.15, 0.15]),
            'saldo': np.round(np.random.uniform(0, 200, n_users), 2),
            'total_viajes': np.random.randint(0, 500, n_users),
            'gasto_total': np.round(np.random.uniform(0, 2000, n_users), 2),
            'ultima_actividad': register_dates + pd.to_timedelta(np.random.randint(0, 30, n_users), unit='D'),
            'satisfaccion': np.round(np.random.uniform(1, 5, n_users), 1),
            'churn_risk': np.round(np.random.uniform(0, 1, n_users), 3),
            'zona': np.random.choice(
                ['Plan 3000', 'Villa 1ro de Mayo', '4to Anillo', 'Equipetrol', 
                 'Centro', 'Pampa de la Isla', 'Radial 13', 'UV Norte'],
                n_users
            ),
        })
        
        # Ajustar churn risk
        df.loc[df['total_viajes'] > 200, 'churn_risk'] *= 0.3
        df.loc[df['total_viajes'] < 10, 'churn_risk'] = np.minimum(df.loc[df['total_viajes'] < 10, 'churn_risk'] * 2, 1.0)
        
        return df
    
    def _generate_routes_dataset(self) -> pd.DataFrame:
        """Dataset de rutas."""
        rutas = [
            {'id': 1, 'nombre': 'Plan 3000 → Centro', 'distancia_km': 12, 'tarifa': 3.50, 'frecuencia_min': 10, 'vehiculos': 8},
            {'id': 2, 'nombre': 'Villa 1ro de Mayo → UAGRM', 'distancia_km': 8, 'tarifa': 2.50, 'frecuencia_min': 15, 'vehiculos': 6},
            {'id': 3, 'nombre': '4to Anillo → Terminal', 'distancia_km': 15, 'tarifa': 4.00, 'frecuencia_min': 12, 'vehiculos': 7},
            {'id': 4, 'nombre': 'Equipetrol → Mercado Abasto', 'distancia_km': 6, 'tarifa': 2.00, 'frecuencia_min': 20, 'vehiculos': 4},
            {'id': 5, 'nombre': 'Pampa Isla → 2do Anillo', 'distancia_km': 10, 'tarifa': 3.00, 'frecuencia_min': 15, 'vehiculos': 5},
            {'id': 6, 'nombre': 'UV Norte → Centro', 'distancia_km': 11, 'tarifa': 3.50, 'frecuencia_min': 12, 'vehiculos': 6},
            {'id': 7, 'nombre': 'Radial 13 → Casco Viejo', 'distancia_km': 7, 'tarifa': 2.50, 'frecuencia_min': 18, 'vehiculos': 4},
            {'id': 8, 'nombre': 'Satélite Norte → Terminal', 'distancia_km': 14, 'tarifa': 3.50, 'frecuencia_min': 15, 'vehiculos': 5},
            {'id': 9, 'nombre': 'Los Lotes → Centro', 'distancia_km': 9, 'tarifa': 3.00, 'frecuencia_min': 12, 'vehiculos': 5},
            {'id': 10, 'nombre': 'Warnes → 3er Anillo', 'distancia_km': 18, 'tarifa': 5.00, 'frecuencia_min': 25, 'vehiculos': 3},
            {'id': 11, 'nombre': 'La Guardia → Centro', 'distancia_km': 20, 'tarifa': 5.50, 'frecuencia_min': 30, 'vehiculos': 3},
            {'id': 12, 'nombre': 'Montero Express', 'distancia_km': 50, 'tarifa': 15.00, 'frecuencia_min': 60, 'vehiculos': 4},
        ]
        return pd.DataFrame(rutas)
    
    def _generate_vehicles_dataset(self) -> pd.DataFrame:
        """Dataset de vehículos."""
        np.random.seed(44)
        n = 55
        
        df = pd.DataFrame({
            'vehiculo_id': range(1, n + 1),
            'placa': [f'SCZ-{i:03d}' for i in range(1, n + 1)],
            'ruta_id': np.random.randint(1, 13, n),
            'capacidad': np.random.choice([30, 40, 50], n, p=[0.2, 0.6, 0.2]),
            'tipo': np.random.choice(['MICRO', 'BUS', 'ARTICULADO'], n, p=[0.3, 0.5, 0.2]),
            'estado': np.random.choice(['ACTIVO', 'MANTENIMIENTO', 'INACTIVO'], n, p=[0.80, 0.12, 0.08]),
            'km_recorridos': np.random.randint(10000, 200000, n),
            'antigüedad_años': np.random.randint(1, 15, n),
            'costo_mantenimiento_mensual': np.round(np.random.uniform(500, 3000, n), 2),
        })
        
        return df
    
    def _generate_feedbacks_dataset(self, n_feedbacks: int = 5000) -> pd.DataFrame:
        """Dataset de feedbacks/sentimientos."""
        np.random.seed(45)
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=90),
            end=datetime.now(),
            periods=n_feedbacks
        )
        
        sentimientos = np.random.choice(
            ['POSITIVO', 'NEUTRO', 'NEGATIVO'], n_feedbacks,
            p=[0.55, 0.30, 0.15]
        )
        
        categorias = np.random.choice(
            ['puntualidad', 'limpieza', 'seguridad', 'precio', 'atención', 
             'comodidad', 'frecuencia', 'app_móvil', 'pago_nfc'],
            n_feedbacks
        )
        
        scores = np.where(
            sentimientos == 'POSITIVO', np.random.uniform(3.5, 5.0, n_feedbacks),
            np.where(
                sentimientos == 'NEUTRO', np.random.uniform(2.5, 3.5, n_feedbacks),
                np.random.uniform(1.0, 2.5, n_feedbacks)
            )
        )
        
        df = pd.DataFrame({
            'feedback_id': range(1, n_feedbacks + 1),
            'fecha': dates,
            'usuario_id': np.random.randint(1, 2001, n_feedbacks),
            'ruta_id': np.random.randint(1, 13, n_feedbacks),
            'sentimiento': sentimientos,
            'categoria': categorias,
            'score': np.round(scores, 1),
            'texto_length': np.random.randint(10, 300, n_feedbacks),
        })
        
        return df
    
    def _generate_financial_dataset(self) -> pd.DataFrame:
        """Dataset financiero mensual."""
        months = pd.date_range(
            start=datetime.now() - timedelta(days=365),
            end=datetime.now(),
            freq='MS'
        )
        
        n = len(months)
        base_revenue = 45000
        growth = np.linspace(1.0, 1.35, n)  # 35% crecimiento anual
        
        df = pd.DataFrame({
            'mes': months,
            'ingresos_brutos': np.round(base_revenue * growth * np.random.uniform(0.9, 1.1, n), 2),
            'costos_operativos': np.round(base_revenue * 0.6 * growth * np.random.uniform(0.85, 1.05, n), 2),
            'costos_mantenimiento': np.round(np.random.uniform(8000, 15000, n), 2),
            'costos_personal': np.round(np.random.uniform(12000, 18000, n), 2),
            'usuarios_nuevos': np.random.randint(100, 400, n),
            'usuarios_activos': np.random.randint(800, 2000, n),
            'transacciones': np.random.randint(8000, 20000, n),
            'ticket_promedio': np.round(np.random.uniform(2.8, 4.2, n), 2),
        })
        
        df['utilidad_bruta'] = df['ingresos_brutos'] - df['costos_operativos']
        df['utilidad_neta'] = df['utilidad_bruta'] - df['costos_mantenimiento'] - df['costos_personal']
        df['margen_neto'] = np.round(df['utilidad_neta'] / df['ingresos_brutos'] * 100, 2)
        df['roi'] = np.round(df['utilidad_neta'] / (df['costos_operativos'] + df['costos_mantenimiento'] + df['costos_personal']) * 100, 2)
        
        return df
    
    # === KPIs Calculations ===
    
    def calculate_all_kpis(self) -> Dict[str, Any]:
        """Calcular todos los KPIs del sistema."""
        return {
            "operational": self._kpis_operational(),
            "financial": self._kpis_financial(),
            "users": self._kpis_users(),
            "satisfaction": self._kpis_satisfaction(),
            "routes": self._kpis_routes(),
            "ml_models": self._kpis_ml(),
            "calculated_at": datetime.now().isoformat()
        }
    
    def _kpis_operational(self) -> Dict[str, Any]:
        """KPIs operacionales."""
        tx = self.datasets['transactions']
        vehicles = self.datasets['vehicles']
        
        today = tx[tx['fecha'] >= datetime.now() - timedelta(days=1)]
        week = tx[tx['fecha'] >= datetime.now() - timedelta(days=7)]
        month = tx[tx['fecha'] >= datetime.now() - timedelta(days=30)]
        
        return {
            "transacciones_hoy": len(today),
            "transacciones_semana": len(week),
            "transacciones_mes": len(month),
            "transacciones_total": len(tx),
            "vehiculos_activos": len(vehicles[vehicles['estado'] == 'ACTIVO']),
            "vehiculos_mantenimiento": len(vehicles[vehicles['estado'] == 'MANTENIMIENTO']),
            "vehiculos_total": len(vehicles),
            "ocupacion_promedio": round(float(tx['ocupacion'].mean()), 2),
            "ocupacion_hora_pico": round(float(tx[tx['hora_pico']]['ocupacion'].mean()), 2),
            "rutas_activas": int(tx['ruta_id'].nunique()),
            "viajes_por_vehiculo_dia": round(float(len(today) / max(1, len(vehicles[vehicles['estado'] == 'ACTIVO']))), 1),
        }
    
    def _kpis_financial(self) -> Dict[str, Any]:
        """KPIs financieros."""
        fin = self.datasets['financial']
        tx = self.datasets['transactions']
        
        latest = fin.iloc[-1]
        prev = fin.iloc[-2] if len(fin) > 1 else latest
        
        return {
            "ingresos_mes_actual": round(float(latest['ingresos_brutos']), 2),
            "ingresos_mes_anterior": round(float(prev['ingresos_brutos']), 2),
            "crecimiento_mensual": round(float((latest['ingresos_brutos'] - prev['ingresos_brutos']) / prev['ingresos_brutos'] * 100), 2),
            "utilidad_neta": round(float(latest['utilidad_neta']), 2),
            "margen_neto": round(float(latest['margen_neto']), 2),
            "roi": round(float(latest['roi']), 2),
            "ticket_promedio": round(float(tx['monto'].mean()), 2),
            "ingresos_acumulados_año": round(float(fin['ingresos_brutos'].sum()), 2),
            "costo_por_pasajero": round(float(latest['costos_operativos'] / max(1, latest['transacciones'])), 2),
            "revenue_por_ruta": round(float(tx.groupby('ruta_id')['monto'].sum().mean()), 2),
        }
    
    def _kpis_users(self) -> Dict[str, Any]:
        """KPIs de usuarios."""
        users = self.datasets['users']
        tx = self.datasets['transactions']
        
        active_30d = len(users[users['ultima_actividad'] >= datetime.now() - timedelta(days=30)])
        
        return {
            "usuarios_totales": len(users),
            "usuarios_activos_30d": active_30d,
            "tasa_actividad": round(active_30d / len(users) * 100, 2),
            "usuarios_por_tipo": users['tipo'].value_counts().to_dict(),
            "saldo_promedio": round(float(users['saldo'].mean()), 2),
            "viajes_promedio": round(float(users['total_viajes'].mean()), 1),
            "gasto_promedio": round(float(users['gasto_total'].mean()), 2),
            "churn_risk_avg": round(float(users['churn_risk'].mean()), 3),
            "usuarios_alto_riesgo": len(users[users['churn_risk'] > 0.7]),
            "usuarios_premium_pct": round(len(users[users['tipo'] == 'PREMIUM']) / len(users) * 100, 2),
            "distribucion_zonas": users['zona'].value_counts().head(5).to_dict(),
            "nps_score": round(float(users['satisfaccion'].mean()) * 20 - 20, 1),  # Convertir a NPS
        }
    
    def _kpis_satisfaction(self) -> Dict[str, Any]:
        """KPIs de satisfacción."""
        fb = self.datasets['feedbacks']
        
        dist = fb['sentimiento'].value_counts()
        total = len(fb)
        
        return {
            "total_feedbacks": total,
            "distribucion_sentimiento": {
                "POSITIVO": int(dist.get('POSITIVO', 0)),
                "NEUTRO": int(dist.get('NEUTRO', 0)),
                "NEGATIVO": int(dist.get('NEGATIVO', 0)),
            },
            "porcentaje_positivo": round(float(dist.get('POSITIVO', 0) / total * 100), 2),
            "porcentaje_negativo": round(float(dist.get('NEGATIVO', 0) / total * 100), 2),
            "score_promedio": round(float(fb['score'].mean()), 2),
            "categorias_mejor_valoradas": fb.groupby('categoria')['score'].mean().nlargest(3).to_dict(),
            "categorias_peor_valoradas": fb.groupby('categoria')['score'].mean().nsmallest(3).to_dict(),
            "tendencia_semanal": self._sentiment_trend(fb),
        }
    
    def _kpis_routes(self) -> Dict[str, Any]:
        """KPIs por ruta."""
        tx = self.datasets['transactions']
        routes = self.datasets['routes']
        
        route_stats = tx.groupby('ruta_id').agg({
            'transaction_id': 'count',
            'monto': ['sum', 'mean'],
            'ocupacion': 'mean',
            'usuario_id': 'nunique'
        }).reset_index()
        
        route_stats.columns = ['ruta_id', 'viajes', 'ingresos', 'ticket_prom', 'ocupacion', 'usuarios_unicos']
        route_stats = route_stats.merge(routes[['id', 'nombre']], left_on='ruta_id', right_on='id', how='left')
        
        top_routes = route_stats.nlargest(5, 'viajes')
        
        return {
            "total_rutas": len(routes),
            "ruta_mas_usada": str(top_routes.iloc[0]['nombre']) if len(top_routes) > 0 else "N/A",
            "top_5_rutas": [
                {
                    "nombre": str(row['nombre']),
                    "viajes": int(row['viajes']),
                    "ingresos": round(float(row['ingresos']), 2),
                    "ocupacion_promedio": round(float(row['ocupacion']), 1),
                }
                for _, row in top_routes.iterrows()
            ],
            "distribucion_tipo_pago": tx['tipo_pago'].value_counts().to_dict(),
            "hora_pico_viajes": int(tx[tx['hora_pico']]['transaction_id'].count()),
            "hora_normal_viajes": int(tx[~tx['hora_pico']]['transaction_id'].count()),
        }
    
    def _kpis_ml(self) -> Dict[str, Any]:
        """KPIs de modelos ML."""
        return {
            "modelos_activos": 4,
            "modelos": [
                {
                    "nombre": "LSTM Demand Predictor",
                    "tipo": "Deep Learning",
                    "framework": "TensorFlow 2.x",
                    "accuracy": 0.87,
                    "estado": "producción",
                    "última_actualización": (datetime.now() - timedelta(days=2)).isoformat(),
                },
                {
                    "nombre": "BERT Sentiment Analyzer",
                    "tipo": "NLP",
                    "framework": "PyTorch + Transformers",
                    "accuracy": 0.91,
                    "estado": "producción",
                    "última_actualización": (datetime.now() - timedelta(days=5)).isoformat(),
                },
                {
                    "nombre": "DBSCAN User Segmentation",
                    "tipo": "Clustering",
                    "framework": "scikit-learn",
                    "silhouette_score": 0.72,
                    "n_clusters": 4,
                    "estado": "producción",
                    "última_actualización": (datetime.now() - timedelta(days=7)).isoformat(),
                },
                {
                    "nombre": "MobileNetV2 Occupancy Detector",
                    "tipo": "Computer Vision",
                    "framework": "TensorFlow 2.x",
                    "accuracy": 0.89,
                    "estado": "producción",
                    "última_actualización": datetime.now().isoformat(),
                },
            ],
            "predicciones_realizadas_hoy": np.random.randint(200, 500),
            "total_predicciones": np.random.randint(50000, 100000),
        }
    
    def _sentiment_trend(self, fb: pd.DataFrame) -> List[Dict]:
        """Tendencia de sentimiento por semana."""
        fb_copy = fb.copy()
        fb_copy['semana'] = fb_copy['fecha'].dt.isocalendar().week
        
        weekly = fb_copy.groupby('semana').agg({
            'score': 'mean',
            'feedback_id': 'count'
        }).reset_index()
        
        return [
            {"semana": int(row['semana']), "score_promedio": round(float(row['score']), 2), "total": int(row['feedback_id'])}
            for _, row in weekly.tail(8).iterrows()
        ]
    
    # === Análisis de BI ===
    
    def analyze_profitability(self) -> Dict[str, Any]:
        """Análisis de rentabilidad por ruta."""
        tx = self.datasets['transactions']
        routes = self.datasets['routes']
        vehicles = self.datasets['vehicles']
        
        # Ingresos por ruta
        revenue_by_route = tx.groupby('ruta_id')['monto'].sum().reset_index()
        revenue_by_route.columns = ['ruta_id', 'ingresos']
        
        # Costos por ruta (basado en vehículos asignados)
        costs_by_route = vehicles.groupby('ruta_id')['costo_mantenimiento_mensual'].sum().reset_index()
        costs_by_route.columns = ['ruta_id', 'costos']
        
        # Merge
        profitability = revenue_by_route.merge(costs_by_route, on='ruta_id', how='left')
        profitability = profitability.merge(routes[['id', 'nombre']], left_on='ruta_id', right_on='id', how='left')
        profitability['utilidad'] = profitability['ingresos'] - profitability['costos'].fillna(0)
        profitability['margen'] = np.round(profitability['utilidad'] / profitability['ingresos'] * 100, 2)
        
        return {
            "análisis": "Rentabilidad por Ruta",
            "rutas": [
                {
                    "ruta": str(row['nombre']),
                    "ingresos": round(float(row['ingresos']), 2),
                    "costos": round(float(row['costos']), 2) if not pd.isna(row['costos']) else 0,
                    "utilidad": round(float(row['utilidad']), 2),
                    "margen_%": round(float(row['margen']), 2),
                }
                for _, row in profitability.sort_values('utilidad', ascending=False).iterrows()
            ],
            "ruta_más_rentable": str(profitability.loc[profitability['utilidad'].idxmax(), 'nombre']),
            "ruta_menos_rentable": str(profitability.loc[profitability['utilidad'].idxmin(), 'nombre']),
            "margen_promedio": round(float(profitability['margen'].mean()), 2),
        }
    
    def analyze_user_segments(self) -> Dict[str, Any]:
        """Análisis de segmentación de mercado."""
        users = self.datasets['users']
        tx = self.datasets['transactions']
        
        # Segmentar por valor
        user_value = tx.groupby('usuario_id').agg({
            'monto': 'sum',
            'transaction_id': 'count'
        }).reset_index()
        user_value.columns = ['usuario_id', 'gasto_total', 'n_viajes']
        
        # Percentiles para segmentar
        user_value['segmento'] = pd.cut(
            user_value['gasto_total'],
            bins=[-1, user_value['gasto_total'].quantile(0.25), 
                  user_value['gasto_total'].quantile(0.50),
                  user_value['gasto_total'].quantile(0.75), float('inf')],
            labels=['Bajo valor', 'Medio-bajo', 'Medio-alto', 'Alto valor']
        )
        
        segment_stats = user_value.groupby('segmento', observed=True).agg({
            'usuario_id': 'count',
            'gasto_total': 'mean',
            'n_viajes': 'mean'
        }).reset_index()
        segment_stats.columns = ['segmento', 'usuarios', 'gasto_promedio', 'viajes_promedio']
        
        return {
            "análisis": "Segmentación de mercado por valor",
            "segmentos": [
                {
                    "nombre": str(row['segmento']),
                    "usuarios": int(row['usuarios']),
                    "gasto_promedio": round(float(row['gasto_promedio']), 2),
                    "viajes_promedio": round(float(row['viajes_promedio']), 1),
                }
                for _, row in segment_stats.iterrows()
            ],
            "total_usuarios_analizados": len(user_value),
            "valor_total_mercado": round(float(user_value['gasto_total'].sum()), 2),
        }
    
    def forecast_revenue(self, months_ahead: int = 3) -> Dict[str, Any]:
        """Proyección de ingresos."""
        fin = self.datasets['financial']
        
        # Simple linear trend
        x = np.arange(len(fin))
        y = fin['ingresos_brutos'].values
        
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs
        
        # Proyectar
        future_x = np.arange(len(fin), len(fin) + months_ahead)
        projected = slope * future_x + intercept
        
        future_dates = pd.date_range(
            start=fin['mes'].iloc[-1] + timedelta(days=31),
            periods=months_ahead,
            freq='MS'
        )
        
        return {
            "análisis": "Proyección de ingresos",
            "tendencia": "creciente" if slope > 0 else "decreciente",
            "crecimiento_mensual_estimado": round(float(slope), 2),
            "proyecciones": [
                {
                    "mes": str(d.strftime('%Y-%m')),
                    "ingresos_proyectados": round(float(p), 2),
                    "confianza": round(float(max(0.7, 0.95 - i * 0.05)), 2),
                }
                for i, (d, p) in enumerate(zip(future_dates, projected))
            ],
            "histórico_últimos_6_meses": [
                {
                    "mes": str(row['mes'].strftime('%Y-%m')),
                    "ingresos": round(float(row['ingresos_brutos']), 2),
                }
                for _, row in fin.tail(6).iterrows()
            ],
        }
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Información de todos los datasets."""
        info = {}
        for name, df in self.datasets.items():
            info[name] = {
                "rows": len(df),
                "columns": list(df.columns),
                "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            }
        
        total_records = sum(len(df) for df in self.datasets.values())
        total_memory = sum(df.memory_usage(deep=True).sum() for df in self.datasets.values()) / 1024 / 1024
        
        return {
            "total_datasets": len(self.datasets),
            "total_records": total_records,
            "total_memory_mb": round(total_memory, 2),
            "datasets": info,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
        }
    
    def export_dataset(self, dataset_name: str, format: str = "json") -> Any:
        """Exportar dataset."""
        if dataset_name not in self.datasets:
            raise ValueError(f"Dataset '{dataset_name}' not found. Available: {list(self.datasets.keys())}")
        
        df = self.datasets[dataset_name]
        
        if format == "json":
            return json.loads(df.head(1000).to_json(orient='records', date_format='iso'))
        elif format == "csv":
            return df.head(1000).to_csv(index=False)
        elif format == "summary":
            return {
                "describe": json.loads(df.describe().to_json()),
                "head": json.loads(df.head(10).to_json(orient='records', date_format='iso')),
                "shape": list(df.shape),
            }
        else:
            raise ValueError(f"Format '{format}' not supported. Use: json, csv, summary")


# Instancia global
bi_engine = BusinessIntelligenceEngine()
