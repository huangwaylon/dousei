# Train Commute Optimizer - Web UI Implementation Plan

## Overview
Implement a modern, interactive web-based UI for visualizing train commute optimization results with full interactivity, map-based station selection, and comprehensive route visualization.

## Architecture Design

### Technology Stack

**Backend:**
- **Flask** - Lightweight web framework (Python 3.11+)
- **Flask-CORS** - Enable cross-origin requests
- **Existing modules** - Reuse `commute_optimizer.py`, `database_manager.py`, `config.py`

**Frontend:**
- **Leaflet.js** - Interactive map library (open-source, no API keys needed)
- **Vanilla JavaScript** - No heavy frameworks, keep it lightweight
- **CSS Grid/Flexbox** - Modern responsive layouts
- **Chart.js** - Optional for data visualization charts

**Data Flow:**
```
User Interface → Flask API → CommuteOptimizer → SQLite DB → Response → UI Update
```

### Project Structure

```
trains/
├── app.py                     # Flask application entry point
├── web/                       # Web application package
│   ├── __init__.py           # Flask app factory
│   ├── api.py                # REST API endpoints
│   ├── views.py              # HTML page routes
│   └── static/               # Static assets
│       ├── css/
│       │   ├── main.css      # Main styles
│       │   └── map.css       # Map-specific styles
│       ├── js/
│       │   ├── app.js        # Main application logic
│       │   ├── map.js        # Map handling
│       │   ├── api-client.js # API communication
│       │   └── ui.js         # UI components
│       └── images/           # Icons and graphics
│           ├── marker-a.png  # Person A marker
│           ├── marker-b.png  # Person B marker
│           └── marker-home.png # Candidate station marker
└── web/templates/            # HTML templates
    ├── base.html            # Base template
    ├── index.html           # Main application page
    └── components/          # Reusable HTML components
        ├── search-panel.html
        ├── results-panel.html
        └── route-details.html
```

## API Endpoints Design

### RESTful API Structure

#### 1. Station Search
```
GET /api/stations/search?q=<query>&limit=<n>
Response: {
  "stations": [
    {
      "id": "odpt.Station:...",
      "title": "六本木",
      "title_en": "Roppongi",
      "railway": "odpt.Railway:TokyoMetro.Hibiya",
      "railway_name": "Hibiya Line",
      "operator": "Tokyo Metro",
      "latitude": 35.6627,
      "longitude": 139.7294
    },
    ...
  ],
  "count": 10
}
```

#### 2. Get All Stations (for map)
```
GET /api/stations/all?operator=<operator>
Response: {
  "stations": [...],
  "count": 1150
}
```

#### 3. Station Details
```
GET /api/stations/<station_id>
Response: {
  "id": "...",
  "title": "...",
  "connections": [...],
  "nearby_stations": [...]
}
```

#### 4. Analyze Commute
```
POST /api/analyze
Request Body: {
  "station_a": "odpt.Station:...",
  "station_b": "odpt.Station:...",
  "top_n": 10,
  "max_time": 120
}
Response: {
  "work_stations": {
    "a": {...},
    "b": {...}
  },
  "candidates": [
    {
      "station_id": "...",
      "station_name": "...",
      "total_time": 57.5,
      "time_difference": 2.5,
      "balance_score": 0.979,
      "latitude": 35.6627,
      "longitude": 139.7294,
      "route_from_a": {
        "total_time": 30.0,
        "total_stops": 8,
        "transfers": 1,
        "segments": [
          {
            "from_station": "...",
            "from_station_name": "...",
            "from_coordinates": [35.66, 139.72],
            "to_station": "...",
            "to_station_name": "...",
            "to_coordinates": [35.67, 139.73],
            "railway": "...",
            "railway_name": "Hibiya Line",
            "travel_time": 12.5,
            "num_stops": 5,
            "is_transfer": false
          },
          ...
        ]
      },
      "route_from_b": {...}
    },
    ...
  ],
  "computation_time": 1.23
}
```

#### 5. Railway Lines
```
GET /api/railways
Response: {
  "railways": [
    {
      "id": "...",
      "title": "...",
      "operator": "...",
      "color": "#..."
    },
    ...
  ]
}
```

## UI Components

### 1. Main Layout (3-Panel Design)

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Train Commute Optimizer                             │
├──────────────┬───────────────────────────────┬──────────────┤
│              │                               │              │
│  Search      │      Interactive Map          │   Results    │
│  Panel       │      (Leaflet.js)             │   Panel      │
│              │                               │              │
│  - Work A    │  - Station markers            │  - Top N     │
│    [Input]   │  - Route lines                │    stations  │
│             │  - Click to select            │  - Details   │
│  - Work B    │  - Hover info                 │  - Filter    │
│    [Input]   │  - Zoom/Pan                   │  - Compare   │
│              │                               │              │
│  [Analyze]   │  - Color-coded paths          │  - Export    │
│              │  - Animation                  │              │
└──────────────┴───────────────────────────────┴──────────────┘
```

**Responsive Behavior:**
- Desktop (>1200px): 3-panel horizontal layout
- Tablet (768-1200px): 2-panel (search + map stacked, results side)
- Mobile (<768px): Single column, collapsible panels

### 2. Search Panel Components

**Station Search Input:**
- Autocomplete dropdown with station suggestions
- Shows: Japanese name, English name, railway line
- Real-time search as user types (debounced)
- Clear button
- Recent searches history

**Analysis Options:**
- Top N results slider (5-20)
- Max commute time slider (30-180 minutes)
- Filter by operators (checkboxes)
- Advanced options (collapsible)

**Action Buttons:**
- "Analyze Routes" - Primary action
- "Reset" - Clear selections
- "Load Example" - Demo data

### 3. Map Component (Leaflet.js)

**Base Map:**
- OpenStreetMap tiles (free, no API key)
- Initial view: Tokyo area (35.6762, 139.6503)
- Zoom levels: 10-16

**Station Markers:**
- **Work Station A** - Red marker (🔴)
- **Work Station B** - Blue marker (🔵)
- **Candidate Stations** - Green markers (🟢), sized by rank
  - Larger = better candidate
  - Label shows rank number
- **Hover** - Show station name and basic info
- **Click** - Select station, show details panel

**Route Lines:**
- **Person A's routes** - Red polylines (dashed)
- **Person B's routes** - Blue polylines (dashed)
- **Common segments** - Purple polylines (solid, thicker)
- Opacity based on selection (selected route = 1.0, others = 0.3)
- Animated "pulse" effect on selected route

**Interactive Features:**
- Click on map to search nearby stations
- Drag markers to update work locations
- Fit bounds to show all routes
- Toggle route visibility (show/hide per person)
- Toggle layers (stations, routes, railways)

**Map Controls:**
- Zoom in/out
- Reset view
- Fullscreen mode
- Layer selector
- Distance ruler (measure tool)

### 4. Results Panel Components

**Results List:**
- Card-based layout, one per candidate station
- Each card shows:
  - Rank badge (#1, #2, etc.)
  - Station name (JP/EN)
  - Total commute time (large, bold)
  - Time difference with color coding:
    - Green: <5 min difference (excellent)
    - Yellow: 5-10 min (good)
    - Orange: 10-15 min (fair)
    - Red: >15 min (poor)
  - Balance score (progress bar)
  - Quick stats (transfers, stops)
  - "View Details" button

**Filtering & Sorting:**
- Sort by: Total time, Balance, Time difference
- Filter by:
  - Max total time
  - Max time difference
  - Min balance score
  - Number of transfers
  - Railway lines used
- Search filter for station names

**Route Details Modal:**
Opens when "View Details" clicked:
- Side-by-side comparison of both routes
- Segment-by-segment breakdown
- Transfer information
- Railway line names with colors
- Time estimates per segment
- Station list with icons
- "Show on Map" button
- "Compare with another" option

**Comparison Mode:**
- Select multiple candidates (checkboxes)
- "Compare Selected" button
- Shows routes overlaid on map
- Side-by-side statistics table
- Export comparison as image/PDF

**Export Options:**
- Export results as JSON
- Export results as CSV
- Save map as image
- Generate PDF report

### 5. Loading & Error States

**Loading States:**
- Skeleton screens for results panel
- Map spinner during data load
- Progress indicator for analysis
- Disable inputs during processing

**Error Handling:**
- Friendly error messages
- Retry buttons
- Validation messages for inputs
- Network error detection
- Fallback for missing data

**Empty States:**
- "No stations found" with suggestions
- "No results" with tips to adjust parameters
- "No route possible" with explanation

## Data Flow & State Management

### State Variables (JavaScript)

```javascript
const appState = {
  // Station selections
  workStationA: null,
  workStationB: null,
  
  // Analysis results
  candidates: [],
  selectedCandidateIndex: null,
  
  // Map state
  map: null,
  markers: {
    workA: null,
    workB: null,
    candidates: []
  },
  routeLayers: [],
  
  // UI state
  isAnalyzing: false,
  viewMode: 'list', // 'list' | 'map' | 'compare'
  filters: {
    maxTotalTime: 120,
    maxTimeDiff: 30,
    minBalance: 0,
    railways: []
  },
  
  // Settings
  topN: 10,
  maxTime: 120
};
```

### Event Flow

1. **Station Selection:**
   ```
   User types in search → API call (debounced) → 
   Display suggestions → User selects → 
   Update state → Add marker to map → Enable analysis button
   ```

2. **Analysis:**
   ```
   User clicks "Analyze" → Validate inputs → 
   Show loading → POST /api/analyze → 
   Receive results → Update state → 
   Render results panel → Draw routes on map → 
   Fit map bounds → Hide loading
   ```

3. **Candidate Selection:**
   ```
   User clicks candidate card → Update selected index → 
   Highlight route on map → Zoom to route → 
   Show route details → Dim other routes
   ```

4. **Filter Change:**
   ```
   User adjusts filter → Update filter state → 
   Re-filter candidates → Update results panel → 
   Update visible routes on map
   ```

## Implementation Details

### Backend (Flask)

**app.py:**
```python
from web import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**web/__init__.py:**
```python
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    from .api import api_bp
    from .views import views_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp)
    
    return app
```

**web/api.py:**
```python
from flask import Blueprint, jsonify, request
from commute_optimizer import CommuteOptimizer
import config

api_bp = Blueprint('api', __name__)
optimizer = CommuteOptimizer(config.DEFAULT_DB_PATH)

@api_bp.route('/stations/search')
def search_stations():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not optimizer.station_info:
        optimizer.build_network()
    
    results = optimizer.search_station(query)[:limit]
    
    stations = []
    for station_id, title, title_en, railway in results:
        info = optimizer.station_info[station_id]
        railway_info = optimizer.railway_info.get(railway, {})
        
        stations.append({
            'id': station_id,
            'title': title,
            'title_en': title_en,
            'railway': railway,
            'railway_name': railway_info.get('title', ''),
            'latitude': info.get('latitude'),
            'longitude': info.get('longitude')
        })
    
    return jsonify({'stations': stations, 'count': len(stations)})

@api_bp.route('/analyze', methods=['POST'])
def analyze_commute():
    data = request.json
    
    station_a = data.get('station_a')
    station_b = data.get('station_b')
    top_n = data.get('top_n', 10)
    max_time = data.get('max_time', 120)
    
    # Validation
    if not station_a or not station_b:
        return jsonify({'error': 'Both stations required'}), 400
    
    # Run analysis
    candidates = optimizer.find_optimal_stations(
        station_a, station_b, top_n, max_time
    )
    
    # Format results with coordinates and detailed routes
    formatted_candidates = []
    for candidate in candidates:
        formatted_candidates.append({
            'station_id': candidate.station_id,
            'station_name': candidate.station_name,
            'total_time': candidate.total_time,
            'time_difference': candidate.time_difference,
            'balance_score': candidate.balance_score,
            'latitude': optimizer.station_info[candidate.station_id]['latitude'],
            'longitude': optimizer.station_info[candidate.station_id]['longitude'],
            'route_from_a': format_route(candidate.route_from_a, optimizer),
            'route_from_b': format_route(candidate.route_from_b, optimizer)
        })
    
    return jsonify({
        'work_stations': {
            'a': get_station_details(station_a, optimizer),
            'b': get_station_details(station_b, optimizer)
        },
        'candidates': formatted_candidates
    })
```

### Frontend (JavaScript)

**Key Functions:**

1. **Station Search with Autocomplete:**
```javascript
async function searchStations(query) {
  const response = await fetch(`/api/stations/search?q=${query}`);
  const data = await response.json();
  displaySuggestions(data.stations);
}

function setupAutocomplete(inputElement, onSelect) {
  let debounceTimer;
  inputElement.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      searchStations(e.target.value);
    }, 300);
  });
}
```

2. **Map Initialization:**
```javascript
function initializeMap() {
  const map = L.map('map').setView([35.6762, 139.6503], 12);
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(map);
  
  return map;
}
```

3. **Route Visualization:**
```javascript
function drawRoute(route, color, map) {
  const coordinates = [];
  
  route.segments.forEach(segment => {
    coordinates.push([segment.from_lat, segment.from_lng]);
    coordinates.push([segment.to_lat, segment.to_lng]);
  });
  
  const polyline = L.polyline(coordinates, {
    color: color,
    weight: 4,
    opacity: 0.7,
    dashArray: route.is_selected ? null : '10, 10'
  }).addTo(map);
  
  return polyline;
}
```

4. **Results Rendering:**
```javascript
function renderResults(candidates) {
  const container = document.getElementById('results-list');
  container.innerHTML = '';
  
  candidates.forEach((candidate, index) => {
    const card = createCandidateCard(candidate, index);
    container.appendChild(card);
  });
}

function createCandidateCard(candidate, rank) {
  const card = document.createElement('div');
  card.className = 'candidate-card';
  card.innerHTML = `
    <div class="rank-badge">#${rank + 1}</div>
    <h3>${candidate.station_name}</h3>
    <div class="time-display">${candidate.total_time.toFixed(1)} min</div>
    <div class="balance-bar" style="--score: ${candidate.balance_score}"></div>
    <div class="details">
      <span>Difference: ${candidate.time_difference.toFixed(1)} min</span>
      <span>Transfers: ${candidate.route_from_a.transfers + candidate.route_from_b.transfers}</span>
    </div>
    <button onclick="showDetails(${rank})">View Details</button>
  `;
  return card;
}
```

## Styling Strategy

### CSS Architecture

**main.css:**
- CSS variables for theming
- Mobile-first responsive design
- Flexbox/Grid layouts
- Smooth transitions
- Accessible colors (WCAG AA)

**Color Scheme:**
```css
:root {
  --color-primary: #2563eb;    /* Blue */
  --color-secondary: #7c3aed;  /* Purple */
  --color-success: #10b981;    /* Green */
  --color-warning: #f59e0b;    /* Orange */
  --color-danger: #ef4444;     /* Red */
  --color-person-a: #ef4444;   /* Person A - Red */
  --color-person-b: #3b82f6;   /* Person B - Blue */
  --color-candidate: #10b981;  /* Candidates - Green */
  --color-background: #f9fafb;
  --color-surface: #ffffff;
  --color-text: #1f2937;
  --color-text-secondary: #6b7280;
  --border-radius: 8px;
  --shadow: 0 1px 3px rgba(0,0,0,0.1);
}
```

**Responsive Breakpoints:**
```css
/* Mobile first */
@media (min-width: 768px) { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1280px) { /* Large desktop */ }
```

## Performance Optimization

### Backend:
1. **Caching:**
   - Cache network graph in memory
   - Cache station search results
   - Use Flask-Caching for API responses

2. **Database:**
   - Add indexes on frequently queried columns
   - Use prepared statements
   - Batch queries where possible

3. **API:**
   - Implement pagination for large datasets
   - Compress responses (gzip)
   - Rate limiting to prevent abuse

### Frontend:
1. **Lazy Loading:**
   - Load map tiles on demand
   - Render visible results only (virtual scrolling)
   - Defer non-critical JavaScript

2. **Debouncing:**
   - Search input (300ms)
   - Map zoom/pan events (150ms)
   - Filter changes (200ms)

3. **Optimization:**
   - Minimize DOM manipulations
   - Use CSS transforms for animations
   - Compress images and assets
   - Bundle and minify JavaScript/CSS

## Testing Strategy

### Backend Tests:
```python
def test_search_stations():
    # Test station search endpoint
    
def test_analyze_commute():
    # Test analysis endpoint with valid data
    
def test_invalid_inputs():
    # Test error handling
    
def test_performance():
    # Test response times under load
```

### Frontend Tests:
- Manual testing for UI interactions
- Browser compatibility (Chrome, Firefox, Safari, Edge)
- Mobile responsive testing
- Accessibility testing (keyboard navigation, screen readers)

## Deployment Considerations

### Development:
```bash
# Install dependencies
uv sync
uv add flask flask-cors

# Run development server
python app.py
```

### Production:
- Use Gunicorn/uWSGI for production server
- Set up reverse proxy (nginx)
- Enable HTTPS
- Configure logging
- Set up monitoring
- Use production database (PostgreSQL instead of SQLite)

## Security Considerations

1. **Input Validation:**
   - Sanitize all user inputs
   - Validate station IDs
   - Limit query parameters

2. **CORS:**
   - Configure allowed origins
   - Restrict methods

3. **Rate Limiting:**
   - Prevent API abuse
   - Implement per-IP limits

4. **Error Handling:**
   - Don't expose internal errors
   - Log security events

## Future Enhancements

1. **Advanced Features:**
   - Save favorite routes
   - User accounts and preferences
   - Share results via URL
   - Multi-stop routing
   - Time-based analysis (rush hour vs off-peak)

2. **Visualization:**
   - 3D route visualization
   - Heat maps for optimal areas
   - Animation of commute simulation
   - Real-time train data integration

3. **Mobile App:**
   - Native iOS/Android apps
   - Offline mode
   - Push notifications

4. **Analytics:**
   - Usage statistics
   - Popular routes
   - Performance metrics

## Implementation Timeline

**Phase 1: Core Setup (Day 1)**
- Set up Flask application structure
- Implement basic API endpoints
- Create base HTML template
- Initialize Leaflet map

**Phase 2: Station Search (Day 2)**
- Implement search autocomplete
- Add station markers to map
- Create station selection UI

**Phase 3: Analysis & Results (Day 3)**
- Implement analysis endpoint
- Create results panel
- Add route visualization

**Phase 4: Interactivity (Day 4)**
- Add filtering and sorting
- Implement route comparison
- Add map interactions

**Phase 5: Polish & Testing (Day 5)**
- Responsive design refinement
- Error handling
- Performance optimization
- Testing and bug fixes

## Dependencies to Add

```toml
[project.dependencies]
flask = ">=3.0.0"
flask-cors = ">=4.0.0"
```

## Success Metrics

- [ ] Can search and select stations via map or search
- [ ] Analysis completes in <2 seconds
- [ ] Routes display clearly on map with color coding
- [ ] Results are filterable and sortable
- [ ] Works on mobile devices (responsive)
- [ ] Handles errors gracefully
- [ ] Export functionality works
- [ ] Performance is acceptable with 100+ stations
- [ ] Code is maintainable and well-documented