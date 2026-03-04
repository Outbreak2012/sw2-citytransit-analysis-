from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SentimentType(str, Enum):
    """Sentiment types"""
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class DemandPredictionRequest(BaseModel):
    """Demand prediction request"""
    route_id: int = Field(..., description="Route ID")
    hours_ahead: int = Field(24, description="Hours to predict ahead")
    include_weather: bool = Field(True, description="Include weather data")
    include_events: bool = Field(True, description="Include special events")


class DemandPredictionResponse(BaseModel):
    """Demand prediction response"""
    route_id: int
    predictions: List[Dict[str, Any]]
    confidence_score: float
    model_version: str
    generated_at: datetime


class UserSegmentationRequest(BaseModel):
    """User segmentation request"""
    min_frequency: Optional[int] = Field(None, description="Minimum usage frequency")
    date_from: Optional[datetime] = Field(None, description="Start date")
    date_to: Optional[datetime] = Field(None, description="End date")
    eps: float = Field(0.5, description="DBSCAN eps parameter")
    min_samples: int = Field(5, description="DBSCAN min_samples parameter")


class UserCluster(BaseModel):
    """User cluster"""
    cluster_id: int
    user_count: int
    avg_frequency: float
    avg_spending: float
    common_routes: List[int]
    peak_hours: List[int]
    characteristics: Dict[str, Any]


class UserSegmentationResponse(BaseModel):
    """User segmentation response"""
    clusters: List[UserCluster]
    outliers_count: int
    total_users: int
    silhouette_score: Optional[float]
    generated_at: datetime


class SentimentAnalysisRequest(BaseModel):
    """Sentiment analysis request"""
    text: str = Field(..., description="Text to analyze")
    source: Optional[str] = Field(None, description="Source of the text")
    user_id: Optional[int] = Field(None, description="User ID")


class SentimentAnalysisResponse(BaseModel):
    """Sentiment analysis response"""
    sentiment: SentimentType
    confidence_score: float
    scores: Dict[str, float]
    analyzed_at: datetime


class KPIResponse(BaseModel):
    """KPI response"""
    total_passengers: int
    total_revenue: float
    avg_occupancy: float
    routes_active: int
    peak_hour: int
    sentiment_avg: float
    generated_at: datetime


class ReportRequest(BaseModel):
    """Report generation request"""
    report_type: str = Field(..., description="Type of report")
    date_from: datetime
    date_to: datetime
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    format: str = Field("json", description="Output format: json, pdf, excel")


class ReportResponse(BaseModel):
    """Report response"""
    report_id: str
    report_type: str
    status: str
    download_url: Optional[str]
    generated_at: datetime
