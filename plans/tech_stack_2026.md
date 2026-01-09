# Updated Technology Stack for 2026

## Recommended Stack (Modernized)

### Backend: **FastAPI** (Recommended over Flask)

**Why FastAPI in 2026:**
```python
# Modern async support
@app.get("/api/stations/search")
async def search_stations(q: str, limit: int = 10):
    # Automatic validation, documentation
    results = await optimizer.search_station_async(q)
    return {"stations": results[:limit]}
```

**Benefits:**
- ✅ Automatic OpenAPI documentation at `/docs`
- ✅ Built-in async/await for better performance
- ✅ Pydantic models for automatic validation
- ✅ Type-safe request/response handling
- ✅ Better error messages and debugging
- ✅ ASGI standard (modern Python web apps)
- ✅ Still simple and Pythonic

**Migration from Flask is minimal:**
```python
# Flask style
@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    # ...

# FastAPI style (better)
@app.post('/api/analyze')
async def analyze(request: AnalyzeRequest):
    # Automatic validation!
    # ...
```

### Frontend: **Modern Vanilla JS with Vite**

**Keep it simple but modern:**
- Vanilla JavaScript with ES modules (no React/Vue overhead)
- Vite for development server (incredibly fast)
- TypeScript optional (recommended for larger projects)
- Leaflet.js 1.9+ for maps
- Modern CSS with Container Queries

**Project Structure:**
```
web/
├── src/
│   ├── main.js          # Entry point
│   ├── api.js           # API client
│   ├── map.js           # Map handling
│   ├── ui.js            # UI components
│   └── styles.css       # Modern CSS
├── public/
│   └── index.html
└── vite.config.js
```

### Alternative: Hybrid Approach (Recommended)

**Use FastAPI for API + Static File Serving:**
```python
# app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# API routes
@app.get("/api/stations/search")
async def search_stations(...):
    ...

# Serve built frontend
app.mount("/static", StaticFiles(directory="web/dist"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("web/dist/index.html")
```

## Updated Dependencies

### pyproject.toml
```toml
[project]
name = "trains"
version = "0.1.0"
description = "Train commute optimizer with interactive web UI"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",  # ASGI server
    "python-dotenv>=1.2.1",
    "requests>=2.32.5",
    "pydantic>=2.9.0",           # Data validation
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "httpx>=0.27.0",              # For testing async
    "mypy>=1.11.0",               # Type checking
]
```

### Frontend (package.json)
```json
{
  "name": "trains-ui",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "vite": "^5.4.0"
  },
  "dependencies": {
    "leaflet": "^1.9.4"
  }
}
```

## Modern API Design with FastAPI

### Type-Safe Models
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class StationInfo(BaseModel):
    id: str
    title: str
    title_en: str
    railway: str
    railway_name: str
    latitude: float
    longitude: float

class AnalyzeRequest(BaseModel):
    station_a: str = Field(..., description="Work station A ID")
    station_b: str = Field(..., description="Work station B ID")
    top_n: int = Field(10, ge=1, le=50)
    max_time: float = Field(120.0, ge=10.0, le=300.0)

class RouteSegment(BaseModel):
    from_station: str
    from_station_name: str
    from_coordinates: List[float]
    to_station: str
    to_station_name: str
    to_coordinates: List[float]
    railway: str
    railway_name: str
    travel_time: float
    num_stops: int
    is_transfer: bool = False

class RouteInfo(BaseModel):
    total_time: float
    total_stops: int
    transfers: int
    segments: List[RouteSegment]

class CandidateStation(BaseModel):
    station_id: str
    station_name: str
    total_time: float
    time_difference: float
    balance_score: float
    latitude: float
    longitude: float
    route_from_a: RouteInfo
    route_from_b: RouteInfo

class AnalyzeResponse(BaseModel):
    work_stations: dict
    candidates: List[CandidateStation]
    computation_time: float
```

### Modern API Endpoints
```python
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI(
    title="Train Commute Optimizer API",
    description="Find optimal living stations for dual commute scenarios",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/api/stations/search",
    response_model=dict,
    summary="Search for stations",
    tags=["Stations"]
)
async def search_stations(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
) -> dict:
    """Search for stations by name (Japanese or English)"""
    # Implementation
    pass

@app.post(
    "/api/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze commute options",
    tags=["Analysis"]
)
async def analyze_commute(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Find optimal living stations for two work locations.
    
    Returns top N stations ranked by total commute time and balance.
    """
    start_time = time.time()
    
    # Validation happens automatically via Pydantic!
    if request.station_a == request.station_b:
        raise HTTPException(
            status_code=400,
            detail="Work stations must be different"
        )
    
    # Run analysis
    candidates = optimizer.find_optimal_stations(
        request.station_a,
        request.station_b,
        request.top_n,
        request.max_time
    )
    
    computation_time = time.time() - start_time
    
    return AnalyzeResponse(
        work_stations={...},
        candidates=[...],
        computation_time=computation_time
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

## Modern Frontend with Vite

### vite.config.js
```javascript
import { defineConfig } from 'vite'

export default defineConfig({
  root: 'web',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### Modern JavaScript (ESM)
```javascript
// web/src/api.js
export class ApiClient {
  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
  }

  async searchStations(query, limit = 10) {
    const params = new URLSearchParams({ q: query, limit });
    const response = await fetch(`${this.baseUrl}/stations/search?${params}`);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async analyzeCommute(stationA, stationB, options = {}) {
    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        station_a: stationA,
        station_b: stationB,
        top_n: options.topN || 10,
        max_time: options.maxTime || 120
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Analysis failed');
    }
    
    return await response.json();
  }
}

// web/src/main.js
import { ApiClient } from './api.js';
import { MapController } from './map.js';
import { UIController } from './ui.js';
import './styles.css';

const api = new ApiClient();
const map = new MapController('map');
const ui = new UIController();

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  ui.init();
  map.init();
  setupEventListeners();
});
```

### Modern CSS
```css
/* Using modern features */
:root {
  --color-primary: oklch(60% 0.15 250);  /* Modern color space */
  --space-sm: 0.5rem;
  --space-md: 1rem;
}

/* Container queries (2026 standard) */
.results-panel {
  container-type: inline-size;
  container-name: results;
}

@container results (min-width: 400px) {
  .candidate-card {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}

/* CSS Layers for organization */
@layer reset, base, components, utilities;

@layer components {
  .btn {
    /* Component styles */
  }
}

/* Modern features */
.map-container {
  /* Subgrid if needed */
  display: grid;
  grid-template-rows: subgrid;
  
  /* Anchor positioning */
  anchor-name: --map;
}
```

## Development Workflow (2026)

### 1. Backend Development
```bash
# Install dependencies
uv sync

# Run FastAPI with hot reload
uv run uvicorn app:app --reload --port 8000

# Type checking
uv run mypy .

# Testing
uv run pytest
```

### 2. Frontend Development
```bash
# Install frontend dependencies
npm install

# Run Vite dev server (with HMR)
npm run dev

# Build for production
npm run build
```

### 3. Production
```bash
# Build frontend
npm run build

# Run with production server
uv run uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Comparison: Flask vs FastAPI

| Feature | Flask (2024-style) | FastAPI (2026-recommended) |
|---------|-------------------|----------------------------|
| Async Support | Limited | ✅ Native ASGI |
| Validation | Manual | ✅ Automatic (Pydantic) |
| Documentation | Manual | ✅ Auto-generated OpenAPI |
| Type Safety | Optional | ✅ Built-in |
| Performance | Good | ✅ Better (async) |
| Learning Curve | Easy | Easy |
| Modern Features | Some | ✅ All latest |

## Recommendation

### Option 1: **FastAPI + Modern Vanilla JS** (Recommended)
- Most modern approach
- Best performance
- Automatic documentation
- Still simple and maintainable
- Aligns with 2026 best practices

### Option 2: Flask + Modern Frontend (Acceptable)
- Familiar Flask patterns
- Still works well
- Easy migration path
- Good for smaller projects

### Option 3: Keep it Super Simple (Also Valid)
- Flask without async
- Plain HTML/CSS/JS
- No build tools
- Fastest to implement
- Easiest to maintain for small team

## My Recommendation for This Project

**Use FastAPI + Vite + Vanilla JS** because:
1. ✅ Modern but not complex
2. ✅ Excellent documentation (auto-generated)
3. ✅ Type-safe APIs prevent bugs
4. ✅ Better performance with async
5. ✅ Still simple enough for one person
6. ✅ Aligns with Python 3.11+ features
7. ✅ Easy to test
8. ✅ Future-proof for 2026+

The migration from Flask to FastAPI is minimal (mostly syntax changes), but the benefits are substantial for a modern web application.

Would you like me to implement with **FastAPI** (recommended) or stick with **Flask** (simpler for immediate start)?