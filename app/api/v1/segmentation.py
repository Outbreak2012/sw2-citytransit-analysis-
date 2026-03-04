from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from app.models.schemas import (
    UserSegmentationRequest,
    UserSegmentationResponse,
    UserCluster
)
from app.ml.dbscan_model import dbscan_segmentation
from app.core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Segmentation"])


@router.post("/segment", response_model=UserSegmentationResponse)
async def segment_users(
    request: UserSegmentationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Segment users using DBSCAN clustering"""
    try:
        logger.info("Segmenting users with DBSCAN...")
        
        # Generate synthetic user data
        users_data = dbscan_segmentation.generate_synthetic_users(num_users=500)
        
        # Update DBSCAN parameters
        dbscan_segmentation.eps = request.eps
        dbscan_segmentation.min_samples = request.min_samples
        
        # Fit model
        fit_result = dbscan_segmentation.fit(users_data)
        
        # Analyze clusters
        clusters, outliers_info = dbscan_segmentation.analyze_clusters(users_data)
        
        # Format response
        cluster_objects = [
            UserCluster(
                cluster_id=c['cluster_id'],
                user_count=c['user_count'],
                avg_frequency=c['avg_frequency'],
                avg_spending=c['avg_spending'],
                common_routes=[1, 2, 3],  # Mock data
                peak_hours=[7, 8, 17, 18],  # Mock data
                characteristics={"description": c['characteristics']}
            )
            for c in clusters
        ]
        
        return UserSegmentationResponse(
            clusters=cluster_objects,
            outliers_count=outliers_info['count'],
            total_users=len(users_data),
            silhouette_score=fit_result['silhouette_score'],
            generated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error segmenting users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters")
async def get_clusters(
    current_user: dict = Depends(get_current_user)
):
    """Get existing user clusters"""
    try:
        logger.info("Getting user clusters...")
        
        # Generate and analyze
        users_data = dbscan_segmentation.generate_synthetic_users(num_users=500)
        dbscan_segmentation.fit(users_data)
        clusters, outliers_info = dbscan_segmentation.analyze_clusters(users_data)
        
        return {
            "clusters": clusters,
            "outliers": outliers_info,
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outliers")
async def get_outliers(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get outlier users"""
    try:
        logger.info(f"Getting top {limit} outliers...")
        
        # Generate and analyze
        users_data = dbscan_segmentation.generate_synthetic_users(num_users=500)
        dbscan_segmentation.fit(users_data)
        
        # Get outliers
        users_data['cluster'] = dbscan_segmentation.labels
        outliers = users_data[users_data['cluster'] == -1].head(limit)
        
        outliers_list = [
            {
                "user_id": int(row['user_id']),
                "usage_frequency": float(row['usage_frequency']),
                "avg_spending": float(row['avg_spending']),
                "route_diversity": float(row['route_diversity']),
                "reason": "Comportamiento atípico detectado por DBSCAN"
            }
            for _, row in outliers.iterrows()
        ]
        
        return {
            "outliers": outliers_list,
            "total_outliers": len(users_data[users_data['cluster'] == -1]),
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting outliers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get user profile with cluster assignment"""
    try:
        logger.info(f"Getting profile for user {user_id}...")
        
        # Generate and analyze
        users_data = dbscan_segmentation.generate_synthetic_users(num_users=500)
        dbscan_segmentation.fit(users_data)
        users_data['cluster'] = dbscan_segmentation.labels
        
        # Find user
        user = users_data[users_data['user_id'] == user_id]
        
        if len(user) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_row = user.iloc[0]
        cluster_id = int(user_row['cluster'])
        
        # Get cluster info
        if cluster_id != -1:
            cluster_data = users_data[users_data['cluster'] == cluster_id]
            cluster_info = {
                "cluster_id": cluster_id,
                "cluster_size": len(cluster_data),
                "description": "Usuario frecuente" if user_row['usage_frequency'] > 15 else "Usuario ocasional"
            }
        else:
            cluster_info = {
                "cluster_id": -1,
                "description": "Outlier - Comportamiento atípico"
            }
        
        return {
            "user_id": user_id,
            "cluster": cluster_info,
            "features": {
                "usage_frequency": float(user_row['usage_frequency']),
                "avg_spending": float(user_row['avg_spending']),
                "route_diversity": float(user_row['route_diversity']),
                "peak_hour_ratio": float(user_row['peak_hour_usage_ratio']),
                "weekend_ratio": float(user_row['weekend_usage_ratio'])
            },
            "generated_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
