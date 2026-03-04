from fastapi import APIRouter, Depends
from app.core.security import get_current_user
import logging
import json
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Model Metrics"])


@router.get("/models")
async def get_model_metrics(current_user: dict = Depends(get_current_user)):
    """
    Get detailed metrics for all ML/DL models
    
    Returns performance metrics, business insights, and technical details
    for DBSCAN, Demand Prediction, and Sentiment Analysis models
    """
    try:
        metrics_path = os.path.join('models', 'training_metrics.json')
        
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            return metrics
        else:
            # Return default metrics if file doesn't exist
            return {
                "message": "Training metrics not found. Run training script first.",
                "status": "metrics_unavailable"
            }
            
    except Exception as e:
        logger.error(f"Error loading model metrics: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@router.get("/summary")
async def get_metrics_summary(current_user: dict = Depends(get_current_user)):
    """
    Get quick summary of model performance
    """
    try:
        metrics_path = os.path.join('models', 'training_metrics.json')
        
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            
            return {
                "dbscan": {
                    "clusters": metrics['dbscan']['metrics']['n_clusters'],
                    "quality_score": metrics['dbscan']['metrics']['silhouette_score'],
                    "users_analyzed": metrics['dbscan']['metrics']['total_users_analyzed']
                },
                "demand_prediction": {
                    "accuracy": metrics['demand_prediction']['metrics']['accuracy'],
                    "error_rate": metrics['demand_prediction']['metrics']['test_mape'],
                    "r2_score": metrics['demand_prediction']['metrics']['test_r2']
                },
                "sentiment_analysis": {
                    "accuracy": metrics['sentiment_analysis']['metrics']['accuracy'] * 100,
                    "f1_score": metrics['sentiment_analysis']['metrics']['f1_score'],
                    "positive_rate": metrics['sentiment_analysis']['sentiment_distribution']['positive']
                },
                "overall_status": "production_ready"
            }
        else:
            return {
                "status": "metrics_not_available",
                "message": "Run training script to generate metrics"
            }
            
    except Exception as e:
        logger.error(f"Error loading metrics summary: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@router.get("/business-insights")
async def get_business_insights(current_user: dict = Depends(get_current_user)):
    """
    Get business insights from ML models
    """
    try:
        metrics_path = os.path.join('models', 'training_metrics.json')
        
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            
            return {
                "user_segmentation": {
                    "insights": metrics['dbscan']['business_insights'],
                    "cluster_profiles": metrics['dbscan']['cluster_profiles']
                },
                "demand_forecasting": {
                    "business_value": metrics['demand_prediction']['business_value'],
                    "accuracy": f"{metrics['demand_prediction']['metrics']['accuracy']}%"
                },
                "sentiment_monitoring": {
                    "insights": metrics['sentiment_analysis']['business_insights'],
                    "sentiment_breakdown": metrics['sentiment_analysis']['sentiment_distribution']
                }
            }
        else:
            return {
                "status": "metrics_not_available"
            }
            
    except Exception as e:
        logger.error(f"Error loading business insights: {e}")
        return {
            "error": str(e),
            "status": "error"
        }
