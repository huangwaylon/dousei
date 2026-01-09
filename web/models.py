"""Pydantic models for type-safe API requests and responses."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class StationInfo(BaseModel):
    """Station information model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="Station unique identifier")
    title: str = Field(..., description="Station name in Japanese")
    title_en: str = Field(..., description="Station name in English")
    railway: str = Field(..., description="Railway line identifier")
    railway_name: str = Field(..., description="Railway line name")
    operator: str = Field(..., description="Operator name")
    latitude: Optional[float] = Field(None, description="Station latitude")
    longitude: Optional[float] = Field(None, description="Station longitude")


class StationSearchResponse(BaseModel):
    """Response model for station search."""
    stations: List[StationInfo]
    count: int = Field(..., description="Number of stations returned")


class AnalyzeRequest(BaseModel):
    """Request model for commute analysis."""
    station_a: str = Field(..., description="Work station A identifier")
    station_b: str = Field(..., description="Work station B identifier")
    top_n: int = Field(10, ge=1, le=50, description="Number of top results to return")
    max_time: float = Field(120.0, ge=10.0, le=300.0, description="Maximum commute time in minutes")


class RouteSegment(BaseModel):
    """A segment of a route between two stations."""
    from_station: str
    from_station_name: str
    from_coordinates: List[float] = Field(..., description="[latitude, longitude]")
    to_station: str
    to_station_name: str
    to_coordinates: List[float] = Field(..., description="[latitude, longitude]")
    railway: str
    railway_name: str
    travel_time: float = Field(..., description="Travel time in minutes")
    num_stops: int = Field(..., description="Number of stops")
    is_transfer: bool = Field(False, description="Is this a transfer segment")


class RouteInfo(BaseModel):
    """Complete route information."""
    total_time: float = Field(..., description="Total travel time in minutes")
    total_stops: int = Field(..., description="Total number of stops")
    transfers: int = Field(..., description="Number of transfers required")
    segments: List[RouteSegment]


class CandidateStation(BaseModel):
    """A candidate living station with routes from both work locations."""
    station_id: str
    station_name: str
    total_time: float = Field(..., description="Total commute time for both people")
    time_difference: float = Field(..., description="Time difference between two commutes")
    balance_score: float = Field(..., ge=0.0, le=1.0, description="Balance score (1.0 = perfect balance)")
    latitude: float
    longitude: float
    route_from_a: RouteInfo
    route_from_b: RouteInfo


class WorkStationInfo(BaseModel):
    """Work station information."""
    id: str
    name: str
    latitude: float
    longitude: float


class AnalyzeResponse(BaseModel):
    """Response model for commute analysis."""
    work_stations: dict = Field(..., description="Information about work stations A and B")
    candidates: List[CandidateStation]
    computation_time: float = Field(..., description="Time taken to compute results in seconds")


class RailwayInfo(BaseModel):
    """Railway line information."""
    id: str
    title: str
    title_en: Optional[str] = None
    operator: str
    color: Optional[str] = None


class RailwaysResponse(BaseModel):
    """Response model for railway list."""
    railways: List[RailwayInfo]
    count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service health status")
    database: str = Field(..., description="Database connection status")
    version: str = Field(..., description="API version")