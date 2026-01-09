"""FastAPI application for train commute optimizer."""

import time
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

import config
from commute_optimizer import CommuteOptimizer, MeetingPoint
from database_manager import TrainDatabaseManager
from web.models import (
    StationInfo,
    StationSearchResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    CandidateStation,
    RouteInfo,
    RouteSegment,
    RailwayInfo,
    RailwaysResponse,
    HealthResponse,
    WorkStationInfo,
)

# Initialize FastAPI app
app = FastAPI(
    title="Train Commute Optimizer API",
    description="Find optimal living stations for dual commute scenarios in Tokyo",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize optimizer
optimizer = CommuteOptimizer(config.DEFAULT_DB_PATH)


def format_route_segment(
    segment: Any, 
    optimizer: CommuteOptimizer
) -> RouteSegment:
    """Format a route segment for API response."""
    from_info = optimizer.station_info.get(segment.from_station, {})
    to_info = optimizer.station_info.get(segment.to_station, {})
    railway_info = optimizer.railway_info.get(segment.railway, {})
    
    return RouteSegment(
        from_station=segment.from_station,
        from_station_name=from_info.get("title", "Unknown"),
        from_coordinates=[
            from_info.get("latitude", 0.0),
            from_info.get("longitude", 0.0)
        ],
        to_station=segment.to_station,
        to_station_name=to_info.get("title", "Unknown"),
        to_coordinates=[
            to_info.get("latitude", 0.0),
            to_info.get("longitude", 0.0)
        ],
        railway=segment.railway,
        railway_name=railway_info.get("title", segment.railway.split(":")[-1]),
        travel_time=segment.travel_time,
        num_stops=segment.num_stops,
        is_transfer=segment.railway == "Transfer"
    )


def format_route(route: Any, optimizer: CommuteOptimizer) -> RouteInfo:
    """Format a complete route for API response."""
    return RouteInfo(
        total_time=route.total_time,
        total_stops=route.total_stops,
        transfers=route.get_transfer_count(),
        segments=[format_route_segment(seg, optimizer) for seg in route.segments]
    )


def format_candidate(
    candidate: MeetingPoint, 
    optimizer: CommuteOptimizer
) -> CandidateStation:
    """Format a candidate station for API response."""
    station_info = optimizer.station_info.get(candidate.station_id, {})
    
    return CandidateStation(
        station_id=candidate.station_id,
        station_name=candidate.station_name,
        total_time=candidate.total_time,
        time_difference=candidate.time_difference,
        balance_score=candidate.balance_score,
        latitude=station_info.get("latitude", 0.0),
        longitude=station_info.get("longitude", 0.0),
        route_from_a=format_route(candidate.route_from_a, optimizer),
        route_from_b=format_route(candidate.route_from_b, optimizer)
    )


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize on startup."""
    print("🚀 Starting Train Commute Optimizer API...")
    print("📊 Building network graph...")
    optimizer.build_network()
    print("✅ Ready to serve requests!")


@app.get("/", include_in_schema=False)
async def read_root() -> FileResponse:
    """Serve the main UI page."""
    web_dir = Path("web/dist")
    if web_dir.exists():
        return FileResponse("web/dist/index.html")
    # Fallback for development
    return FileResponse("web/public/index.html")


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"]
)
async def health_check() -> HealthResponse:
    """Check API health status."""
    try:
        with TrainDatabaseManager(config.DEFAULT_DB_PATH) as db:
            db.cursor.execute("SELECT COUNT(*) FROM stations")
            db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        version="1.0.0"
    )


@app.get(
    "/api/stations/search",
    response_model=StationSearchResponse,
    summary="Search for stations",
    tags=["Stations"]
)
async def search_stations(
    q: str = Query(..., min_length=1, description="Search query (Japanese or English)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
) -> StationSearchResponse:
    """
    Search for stations by name.
    
    Searches both Japanese and English station names.
    Returns station information including coordinates for map display.
    """
    if not optimizer.station_info:
        optimizer.build_network()
    
    results = optimizer.search_station(q)[:limit]
    
    stations: List[StationInfo] = []
    for station_id, title, title_en, railway in results:
        info = optimizer.station_info.get(station_id, {})
        railway_info = optimizer.railway_info.get(railway, {})
        
        # Get operator from railway
        operator = "Unknown"
        if "JR-East" in railway:
            operator = "JR East"
        elif "TokyoMetro" in railway:
            operator = "Tokyo Metro"
        elif "Keikyu" in railway:
            operator = "Keikyu"
        
        stations.append(StationInfo(
            id=station_id,
            title=title,
            title_en=title_en,
            railway=railway,
            railway_name=railway_info.get("title", railway.split(":")[-1]),
            operator=operator,
            latitude=info.get("latitude"),
            longitude=info.get("longitude")
        ))
    
    return StationSearchResponse(
        stations=stations,
        count=len(stations)
    )


@app.get(
    "/api/stations/{station_id}",
    response_model=StationInfo,
    summary="Get station details",
    tags=["Stations"]
)
async def get_station(station_id: str) -> StationInfo:
    """Get detailed information about a specific station."""
    if not optimizer.station_info:
        optimizer.build_network()
    
    if station_id not in optimizer.station_info:
        raise HTTPException(status_code=404, detail="Station not found")
    
    info = optimizer.station_info[station_id]
    railway = info.get("railway", "")
    railway_info = optimizer.railway_info.get(railway, {})
    
    operator = "Unknown"
    if "JR-East" in railway:
        operator = "JR East"
    elif "TokyoMetro" in railway:
        operator = "Tokyo Metro"
    elif "Keikyu" in railway:
        operator = "Keikyu"
    
    return StationInfo(
        id=station_id,
        title=info.get("title", ""),
        title_en=info.get("title_en", ""),
        railway=railway,
        railway_name=railway_info.get("title", ""),
        operator=operator,
        latitude=info.get("latitude"),
        longitude=info.get("longitude")
    )


@app.post(
    "/api/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze commute options",
    tags=["Analysis"]
)
async def analyze_commute(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Find optimal living stations for two work locations.
    
    Analyzes the train network to find stations that minimize total commute time
    while maintaining good balance between both commuters.
    
    Returns top N stations ranked by:
    1. Minimum total commute time
    2. Best balance (equal commute times)
    """
    start_time = time.time()
    
    # Validation
    if request.station_a == request.station_b:
        raise HTTPException(
            status_code=400,
            detail="Work stations must be different"
        )
    
    if not optimizer.network_graph:
        optimizer.build_network()
    
    # Verify stations exist
    if request.station_a not in optimizer.station_info:
        raise HTTPException(
            status_code=404,
            detail=f"Station A not found: {request.station_a}"
        )
    
    if request.station_b not in optimizer.station_info:
        raise HTTPException(
            status_code=404,
            detail=f"Station B not found: {request.station_b}"
        )
    
    # Run analysis
    try:
        candidates = optimizer.find_optimal_stations(
            work_station_a=request.station_a,
            work_station_b=request.station_b,
            top_n=request.top_n,
            max_time=request.max_time
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
    
    if not candidates:
        raise HTTPException(
            status_code=404,
            detail="No common reachable stations found. Try increasing max_time."
        )
    
    # Format work station info
    station_a_info = optimizer.station_info.get(request.station_a, {})
    station_b_info = optimizer.station_info.get(request.station_b, {})
    
    work_stations = {
        "a": {
            "id": request.station_a,
            "name": station_a_info.get("title", "Unknown"),
            "latitude": station_a_info.get("latitude", 0.0),
            "longitude": station_a_info.get("longitude", 0.0)
        },
        "b": {
            "id": request.station_b,
            "name": station_b_info.get("title", "Unknown"),
            "latitude": station_b_info.get("latitude", 0.0),
            "longitude": station_b_info.get("longitude", 0.0)
        }
    }
    
    # Format candidates
    formatted_candidates = [format_candidate(c, optimizer) for c in candidates]
    
    computation_time = time.time() - start_time
    
    return AnalyzeResponse(
        work_stations=work_stations,
        candidates=formatted_candidates,
        computation_time=computation_time
    )


@app.get(
    "/api/railways",
    response_model=RailwaysResponse,
    summary="List all railway lines",
    tags=["Railways"]
)
async def list_railways() -> RailwaysResponse:
    """Get list of all railway lines in the system."""
    if not optimizer.railway_info:
        optimizer.build_network()
    
    railways: List[RailwayInfo] = []
    for railway_id, info in optimizer.railway_info.items():
        operator = "Unknown"
        if "JR-East" in railway_id:
            operator = "JR East"
        elif "TokyoMetro" in railway_id:
            operator = "Tokyo Metro"
        elif "Keikyu" in railway_id:
            operator = "Keikyu"
        
        railways.append(RailwayInfo(
            id=railway_id,
            title=info.get("title", ""),
            title_en=info.get("title_en"),
            operator=operator,
            color=None  # Can be added from database if needed
        ))
    
    railways.sort(key=lambda x: (x.operator, x.title))
    
    return RailwaysResponse(
        railways=railways,
        count=len(railways)
    )


# Mount static files for production
web_dist = Path("web/dist")
if web_dist.exists():
    app.mount("/static", StaticFiles(directory="web/dist"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )