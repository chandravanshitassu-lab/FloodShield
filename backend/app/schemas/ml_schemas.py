"""
FloodShield - API Schemas
=========================
Pydantic models defining the request and response structures for the FloodShield
flood risk inference API.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class FloodRiskPredictionRequest(BaseModel):
    """
    Input features payload for district flood risk classification.
    Matches the 33 features used during model training with default values.
    """
    district_name: Optional[str] = Field(default=None, description="Name of the district (for reporting/metadata)")
    state: str = Field(default="Unknown", description="State name for the district")

    # Inundation exposure metrics
    corrected_percent_flooded_area: float = Field(default=0.0, description="Corrected flooded area percentage")
    percent_flooded_area: float = Field(default=0.0, description="Gross flooded area percentage")
    permanent_water_percent: float = Field(default=0.0, description="Baseline permanent water body percentage")

    # Historical flood event statistics (1967-2023)
    total_flood_events: float = Field(default=0.0, description="Total historical flood occurrences recorded")
    total_flood_duration_days: float = Field(default=0.0, description="Cumulative flood duration in days")
    avg_flood_duration_days: float = Field(default=0.0, description="Average flood duration per event in days")
    max_flood_duration_days: float = Field(default=0.0, description="Maximum single flood duration in days")

    # Impact and vulnerability metrics
    total_human_fatalities: float = Field(default=0.0, description="Total cumulative human fatalities")
    avg_human_fatalities_per_event: float = Field(default=0.0, description="Average fatalities per flood event")
    max_human_fatalities_single_event: float = Field(default=0.0, description="Maximum fatalities in a single flood event")
    total_human_injured: float = Field(default=0.0, description="Total reported human injuries")
    total_human_displaced: float = Field(default=0.0, description="Total reported displaced population")
    total_animal_fatalities: float = Field(default=0.0, description="Total reported livestock/animal fatalities")

    # Temporal & trigger hazard metrics
    monsoon_flood_events: float = Field(default=0.0, description="Number of flood events during monsoon months (Jun-Dec)")
    heavy_rain_flood_events: float = Field(default=0.0, description="Number of events triggered by heavy rains/cloudbursts")
    recent_flood_events_2010_2023: float = Field(default=0.0, description="Flood occurrences in the recent decade (2010-2023)")
    has_historical_flood_record: int = Field(default=0, description="1 if district exists in historical inventory, 0 otherwise")

    # Precipitation and seasonal anomaly metrics (optional/district-level)
    has_detailed_rainfall_data: int = Field(default=0, description="1 if detailed rainfall metrics are present, 0 otherwise")
    actual_rainfall_sw_monsoon_mm: Optional[float] = Field(default=None, description="Actual SW monsoon rainfall (mm)")
    normal_rainfall_sw_monsoon_mm: Optional[float] = Field(default=None, description="Normal SW monsoon rainfall (mm)")
    sw_monsoon_departure_percent: Optional[float] = Field(default=None, description="SW monsoon departure percentage")
    actual_rainfall_ne_monsoon_mm: Optional[float] = Field(default=None, description="Actual NE monsoon rainfall (mm)")
    normal_rainfall_ne_monsoon_mm: Optional[float] = Field(default=None, description="Normal NE monsoon rainfall (mm)")
    ne_monsoon_departure_percent: Optional[float] = Field(default=None, description="NE monsoon departure percentage")
    actual_rainfall_winter_mm: Optional[float] = Field(default=None, description="Actual winter rainfall (mm)")
    normal_rainfall_winter_mm: Optional[float] = Field(default=None, description="Normal winter rainfall (mm)")
    actual_rainfall_hot_weather_mm: Optional[float] = Field(default=None, description="Actual hot weather rainfall (mm)")
    normal_rainfall_hot_weather_mm: Optional[float] = Field(default=None, description="Normal hot weather rainfall (mm)")
    total_actual_rainfall_mm: Optional[float] = Field(default=None, description="Total annual actual rainfall (mm)")
    total_normal_rainfall_mm: Optional[float] = Field(default=None, description="Total annual normal rainfall (mm)")
    annual_rainfall_departure_percent: Optional[float] = Field(default=None, description="Total annual departure percentage")
    monsoon_intensity_ratio: Optional[float] = Field(default=None, description="Ratio of monsoon rainfall to annual total")

    class Config:
        json_schema_extra = {
            "example": {
                "district_name": "Patna",
                "state": "Bihar",
                "corrected_percent_flooded_area": 18.82,
                "percent_flooded_area": 19.5,
                "permanent_water_percent": 0.68,
                "total_flood_events": 71.0,
                "total_flood_duration_days": 650.0,
                "avg_flood_duration_days": 9.15,
                "max_flood_duration_days": 45.0,
                "total_human_fatalities": 1250.0,
                "avg_human_fatalities_per_event": 17.6,
                "max_human_fatalities_single_event": 250.0,
                "total_human_injured": 80.0,
                "total_human_displaced": 5000.0,
                "total_animal_fatalities": 3500.0,
                "monsoon_flood_events": 68.0,
                "heavy_rain_flood_events": 45.0,
                "recent_flood_events_2010_2023": 25.0,
                "has_historical_flood_record": 1,
                "has_detailed_rainfall_data": 0
            }
        }


class FloodRiskPredictionResponse(BaseModel):
    """
    Response model containing predicted risk classification and probability distribution.
    """
    district_name: Optional[str] = Field(default=None, description="District name from request")
    state: Optional[str] = Field(default=None, description="State name from request")
    flood_risk_level: str = Field(..., description="Predicted baseline risk tier: 'Low', 'Moderate', 'High', 'Very High'")
    confidence: float = Field(..., description="Confidence probability of the predicted class (0.0 to 1.0)")
    probabilities: Dict[str, float] = Field(..., description="Probability score for each available risk level")
    summary: Optional[str] = Field(default=None, description="Summary description of the prediction")


class HealthResponse(BaseModel):
    """
    Health check status response model.
    """
    status: str = Field(..., description="API operational status")
    model_loaded: bool = Field(..., description="True if ML model pipeline is loaded")
    model_classes: list = Field(default=[], description="Available prediction classes")
    message: str = Field(..., description="Descriptive status message")


class PrioritizedProduct(BaseModel):
    """Single inventory item after flood-risk prioritization."""
    product_id: int
    name: str
    category: str
    price: float
    stock_quantity: int
    inventory_value: float
    vulnerability_score: float
    priority_score: float
    priority_level: str
    recommended_action: str
    reason: str


class InventoryPrioritizeResponse(BaseModel):
    """Response for POST /inventory/prioritize."""
    flood_risk_level: str
    scoring_type: str
    products: list[PrioritizedProduct]
