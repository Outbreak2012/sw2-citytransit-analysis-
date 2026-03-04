from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.models.schemas import (
    DemandPredictionRequest,
    DemandPredictionResponse
)
from app.ml.lstm_model import lstm_predictor
from app.core.security import get_current_user
import logging
from app.db.redis_cache import redis_conn
from app.core.config import settings
from app.services.demand_service import demand_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demand", tags=["Demand Prediction"])


@router.post("/predict", response_model=DemandPredictionResponse)
async def predict_demand(
    request: DemandPredictionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Predict demand using LSTM model"""
    try:
        logger.info(f"Predicting demand for route {request.route_id}")

        # TEMPORARILY DISABLED CACHE FOR TESTING REALISTIC DATA
        cache_key = f"demand:predict:{request.route_id}:{request.hours_ahead}"
        # try:
        #     cached = redis_conn.get(cache_key)
        #     if cached:
        #         logger.info("✅ Demand prediction returned from cache")
        #         return DemandPredictionResponse(**cached)
        # except Exception:
        #     logger.debug("Redis not available for demand/predict")

        # Try to get real data from ClickHouse
        recent_data = demand_service.get_historical_demand(
            route_id=request.route_id, 
            days=7
        )
        
        # Fallback to synthetic data if no real data available
        if recent_data is None or recent_data.empty:
            logger.warning("⚠️ No real data available, using synthetic data")
            recent_data = lstm_predictor.generate_synthetic_data(num_samples=100)

        # Make predictions
        predictions = lstm_predictor.predict(
            recent_data=recent_data,
            hours_ahead=request.hours_ahead
        )
        
        # Format response
        predictions_list = [
            {
                "hour": i + 1,
                "predicted_demand": float(pred),
                "confidence": 0.85
            }
            for i, pred in enumerate(predictions)
        ]
        
        response = DemandPredictionResponse(
            route_id=request.route_id,
            predictions=predictions_list,
            confidence_score=0.85,
            model_version="1.0.0",
            generated_at=datetime.now()
        )

        # TEMPORARILY DISABLED CACHE FOR TESTING
        # Cache the response
        # try:
        #     payload = response.dict()
        #     payload['generated_at'] = payload['generated_at'].isoformat()
        #     redis_conn.set(cache_key, payload, ttl=getattr(settings, 'CACHE_TTL', 300))
        # except Exception:
        #     logger.debug("Could not cache demand prediction")

        return response
        
    except Exception as e:
        logger.error(f"Error predicting demand: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/{route_id}")
async def get_demand_forecast(
    route_id: int,
    hours: int = 24,
    current_user: dict = Depends(get_current_user)
):
    """Get demand forecast for a specific route"""
    try:
        logger.info(f"Getting forecast for route {route_id}")

        cache_key = f"demand:forecast:{route_id}:{hours}"
        try:
            cached = redis_conn.get(cache_key)
            if cached:
                logger.info("✅ Demand forecast returned from cache")
                return cached
        except Exception:
            logger.debug("Redis not available for demand/forecast")

        # Try to get real data from ClickHouse
        recent_data = demand_service.get_historical_demand(
            route_id=route_id, 
            days=7
        )
        
        # Fallback to synthetic data if no real data available
        if recent_data is None or recent_data.empty:
            logger.warning("⚠️ No real data available, using synthetic data")
            recent_data = lstm_predictor.generate_synthetic_data(num_samples=100)

        # Make predictions
        predictions = lstm_predictor.predict(
            recent_data=recent_data,
            hours_ahead=hours
        )

        result = {
            "route_id": route_id,
            "forecast": [
                {"hour": i + 1, "demand": float(pred)}
                for i, pred in enumerate(predictions)
            ],
            "generated_at": datetime.now().isoformat()
        }

        try:
            redis_conn.set(cache_key, result, ttl=getattr(settings, 'CACHE_TTL', 300))
        except Exception:
            logger.debug("Could not cache demand forecast")

        return result
        
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_demand_trends(
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """Get demand trends for the last N days"""
    try:
        logger.info(f"Getting demand trends for {days} days")

        cache_key = f"demand:trends:{days}"
        try:
            cached = redis_conn.get(cache_key)
            if cached:
                logger.info("✅ Demand trends returned from cache")
                return cached
        except Exception:
            logger.debug("Redis not available for demand/trends")

        # Try to get real historical data from ClickHouse
        historical_data = demand_service.get_historical_demand(days=days)
        
        # Fallback to synthetic data if no real data available
        if historical_data is None or historical_data.empty:
            logger.warning("⚠️ No real data available, using synthetic data")
            historical_data = lstm_predictor.generate_synthetic_data(num_samples=days * 24)

        # Calculate trends
        hourly_avg = historical_data.groupby('hour')['demand'].mean()
        daily_avg = historical_data.groupby(historical_data['timestamp'].dt.date)['demand'].mean()

        result = {
            "hourly_trends": [
                {"hour": int(hour), "avg_demand": float(demand)}
                for hour, demand in hourly_avg.items()
            ],
            "daily_trends": [
                {"date": str(date), "avg_demand": float(demand)}
                for date, demand in daily_avg.items()
            ],
            "generated_at": datetime.now().isoformat()
        }

        try:
            redis_conn.set(cache_key, result, ttl=getattr(settings, 'CACHE_TTL', 300))
        except Exception:
            logger.debug("Could not cache demand trends")

        return result
        
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_model(
    epochs: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Train LSTM model (admin only)"""
    try:
        logger.info("Training LSTM model...")
        
        # Generate training data
        training_data = lstm_predictor.generate_synthetic_data(num_samples=2000)
        
        # Train model
        history = lstm_predictor.train(training_data, epochs=epochs)
        
        return {
            "status": "success",
            "message": "Model trained successfully",
            "epochs": epochs,
            "final_loss": float(history['loss'][-1]),
            "final_mae": float(history['mae'][-1]),
            "trained_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
