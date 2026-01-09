# Train Commute Optimizer - Web UI Guide

Modern web-based UI for finding optimal living stations for dual commute scenarios in Tokyo.

## Features

✨ **Interactive Map**: Leaflet.js-powered map with station markers and route visualization
🔍 **Smart Search**: Real-time autocomplete for station search in Japanese and English  
📊 **Results Panel**: Sortable, filterable results with detailed route information
🎨 **Modern Design**: Responsive UI with smooth animations and transitions
📱 **Mobile Friendly**: Works great on desktop, tablet, and mobile devices
💾 **Export Options**: Download results as JSON or CSV
🚀 **Fast API**: FastAPI backend with automatic OpenAPI documentation
📖 **Auto Docs**: Interactive API documentation at `/api/docs`

## Technology Stack (2026)

### Backend
- **FastAPI 0.115+** - Modern async Python web framework
- **Pydantic 2.9+** - Type-safe data validation
- **Uvicorn** - ASGI server with hot reload
- **Python 3.11+** - Latest Python features

### Frontend
- **Vanilla JavaScript** - Modern ES modules, no frameworks
- **Vite 5.4+** - Lightning-fast dev server and build tool
- **Leaflet.js 1.9+** - Interactive maps (no API keys needed)
- **Modern CSS** - CSS Grid, Flexbox, Container Queries

## Quick Start

### 1. Install Backend Dependencies

```bash
# Using uv (recommended)
uv sync

# This will install:
# - fastapi>=0.115.0
# - uvicorn[standard]>=0.30.0
# - pydantic>=2.9.0
# - python-dotenv>=1.2.1
# - requests>=2.32.5
```

### 2. Setup Database

Make sure you have the train data populated:

```bash
# Fetch train data (if not already done)
python cli.py fetch
```

### 3. Install Frontend Dependencies

```bash
cd web
npm install

# This will install:
# - vite@^5.4.0
# - leaflet@^1.9.4
```

### 4. Run Development Servers

**Terminal 1 - Backend:**
```bash
# From project root
uv run uvicorn app:app --reload --port 8000

# Or with Python directly
python app.py
```

**Terminal 2 - Frontend:**
```bash
# From web directory
cd web
npm run dev

# Vite dev server will run on http://localhost:3456
```

### 5. Access the Application

- **Web UI**: http://localhost:3456
- **API Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Project Structure

```
trains/
├── app.py                          # FastAPI application
├── web/
│   ├── models.py                   # Pydantic models
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.js              # Vite configuration
│   └── public/
│       ├── index.html              # Main HTML page
│       └── src/
│           ├── main.js             # App entry point
│           ├── api.js              # API client
│           ├── map.js              # Map controller
│           ├── ui.js               # UI controller
│           └── styles.css          # Modern CSS
├── commute_optimizer.py            # Core optimization logic
├── database_manager.py             # Database operations
├── config.py                       # Configuration
└── data_fetcher.py                 # Data fetching
```

## Using the Web UI

### Step 1: Search for Work Stations

1. **Person A's Work Station**
   - Type in the search box (Japanese or English)
   - Autocomplete suggestions appear
   - Click a suggestion to select
   - Red marker appears on map

2. **Person B's Work Station**
   - Same process as Person A
   - Blue marker appears on map

### Step 2: Configure Options (Optional)

- **Top Results**: Adjust slider (5-20 stations)
- **Max Commute Time**: Adjust slider (30-180 minutes)

### Step 3: Analyze

Click the **"Analyze Routes"** button.

The system will:
- Calculate optimal routes using Dijkstra's algorithm
- Find stations reachable by both people
- Rank by total time and balance
- Display results in ~1-2 seconds

### Step 4: Explore Results

**Results Panel (Right):**
- View top N candidate stations
- See total time, balance score, and time difference
- Click any card to highlight on map
- Click "View Details" for route breakdown

**Map (Center):**
- 🔴 Red marker = Person A's work
- 🔵 Blue marker = Person B's work  
- 🟢 Green markers = Candidate stations (numbered by rank)
- Red/Blue lines = Routes to candidate stations
- Click candidate markers for quick info

**Map Controls:**
- 🎯 **Fit View** - Zoom to show all routes
- 👁️ **Toggle Routes** - Show/hide route lines

### Step 5: View Details

Click "View Details" on any candidate to see:
- Side-by-side route comparison
- Segment-by-segment breakdown
- Transfer information
- Station-to-station times

### Step 6: Export Results

Use the export buttons to download:
- 💾 **JSON** - Full data with all routes
- 📊 **CSV** - Spreadsheet-friendly format

## API Endpoints

### Station Search
```
GET /api/stations/search?q={query}&limit={n}
```

### Analyze Commute
```
POST /api/analyze
{
  "station_a": "odpt.Station:...",
  "station_b": "odpt.Station:...",
  "top_n": 10,
  "max_time": 120
}
```

### Get Station
```
GET /api/stations/{station_id}
```

### List Railways
```
GET /api/railways
```

### Health Check
```
GET /api/health
```

Full interactive documentation at: **http://localhost:8000/api/docs**

## Building for Production

### 1. Build Frontend

```bash
cd web
npm run build

# Outputs to web/dist/
```

### 2. Run Production Server

```bash
# Single worker
uv run uvicorn app:app --host 0.0.0.0 --port 8000

# Multiple workers (production)
uv run uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

The FastAPI app will serve:
- API endpoints at `/api/*`
- Built frontend at `/`
- Static files from `web/dist/`

### 3. Production Deployment Options

**Option A: Simple (Single Server)**
```bash
# Install production dependencies
uv sync

# Build frontend
cd web && npm run build && cd ..

# Run with Uvicorn
uv run uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

**Option B: With Nginx (Recommended)**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /path/to/trains/web/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

**Option C: Docker**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install uv && uv sync

# Install Node and build frontend
RUN apt-get update && apt-get install -y nodejs npm
RUN cd web && npm install && npm run build

# Run app
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Development Tips

### Hot Reload

Both servers support hot reload:
- **Backend**: Uvicorn auto-reloads on Python file changes
- **Frontend**: Vite HMR (Hot Module Replacement) for instant updates

### Debugging

**Backend:**
```python
# Add debug logs in app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
// Access controllers in browser console
window.app.map    // Map controller
window.app.ui     // UI controller  
window.app.api    // API client
```

### Type Checking

```bash
# Check Python types
uv run mypy app.py web/models.py

# Lint Python code
uv run ruff check .
```

## Performance Optimization

### Backend
- Network graph cached in memory (fast subsequent analyses)
- Gzip compression enabled
- Async/await for non-blocking requests

### Frontend
- Debounced search (300ms)
- Virtual scrolling for large result lists
- CSS transforms for smooth animations
- Minimal DOM manipulations

## Keyboard Shortcuts

- **Enter** - Analyze (when both stations selected)
- **Esc** - Close modal

## Browser Support

- Chrome/Edge 120+ ✅
- Firefox 120+ ✅
- Safari 17+ ✅
- Mobile browsers ✅

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Use different port
uvicorn app:app --reload --port 8001
```

**Database not found:**
```bash
# Populate database first
python cli.py fetch
```

**Import errors:**
```bash
# Reinstall dependencies
uv sync --force
```

### Frontend Issues

**Vite not starting:**
```bash
# Clear cache and reinstall
cd web
rm -rf node_modules package-lock.json
npm install
```

**API calls failing:**
- Check backend is running on port 8000
- Check CORS settings in `app.py`
- Verify proxy config in `vite.config.js`

**Map not loading:**
- Check internet connection (loads tiles from OpenStreetMap)
- Check browser console for errors
- Verify Leaflet CSS is loaded

## Advanced Features

### Custom Styling

Edit `web/public/src/styles.css`:
```css
:root {
  --color-primary: #your-color;
  --color-station-a: #your-color;
  --color-station-b: #your-color;
}
```

### Add New API Endpoints

1. Add Pydantic model in `web/models.py`
2. Add endpoint in `app.py`
3. Use in frontend via `api.js`

Example:
```python
# web/models.py
class MyRequest(BaseModel):
    field: str

# app.py
@app.post("/api/my-endpoint")
async def my_endpoint(request: MyRequest):
    return {"result": "success"}
```

## Contributing

When adding features:
1. ✅ Follow existing code style
2. ✅ Add type hints (Python)
3. ✅ Update documentation
4. ✅ Test on mobile devices
5. ✅ Check API docs still generate

## Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Vite**: https://vitejs.dev/
- **Leaflet**: https://leafletjs.com/
- **Python uv**: https://github.com/astral-sh/uv

## License

Same as main project license.

## Support

For issues:
1. Check this README
2. Check API docs at `/api/docs`
3. Check browser console for errors
4. Check backend logs
5. Review `plans/` directory for architecture details