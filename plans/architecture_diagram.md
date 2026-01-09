# Train Commute Optimizer - Architecture Diagram

## System Architecture

```mermaid
graph TB
    subgraph Client["Client Browser"]
        UI[Web UI]
        MAP[Leaflet Map]
        SEARCH[Search Panel]
        RESULTS[Results Panel]
    end
    
    subgraph Backend["Flask Backend"]
        API[REST API]
        VIEWS[Views Blueprint]
    end
    
    subgraph Core["Core Modules"]
        OPT[CommuteOptimizer]
        DB[DatabaseManager]
        FETCH[DataFetcher]
    end
    
    subgraph Data["Data Layer"]
        SQLITE[(SQLite DB)]
        CACHE[In-Memory Cache]
    end
    
    UI --> MAP
    UI --> SEARCH
    UI --> RESULTS
    
    SEARCH -->|AJAX| API
    RESULTS -->|AJAX| API
    MAP -->|AJAX| API
    
    API --> OPT
    API --> DB
    
    OPT --> DB
    OPT --> CACHE
    
    DB --> SQLITE
    FETCH --> SQLITE
```

## Data Flow - Station Analysis

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Web UI
    participant API as Flask API
    participant OPT as CommuteOptimizer
    participant DB as Database
    
    U->>UI: Enter Work Stations A & B
    UI->>API: POST /api/analyze
    API->>OPT: find_optimal_stations()
    OPT->>DB: Load network graph
    DB-->>OPT: Stations & Railways
    OPT->>OPT: Run Dijkstra's algorithm
    OPT->>OPT: Find common stations
    OPT->>OPT: Calculate balance scores
    OPT-->>API: Candidate stations + routes
    API-->>UI: JSON response
    UI->>UI: Render results panel
    UI->>UI: Draw routes on map
    UI-->>U: Display results
```

## Component Interaction

```mermaid
graph LR
    subgraph Frontend
        A[Search Input] --> B[API Client]
        C[Map Component] --> B
        D[Results List] --> B
    end
    
    subgraph API Layer
        B --> E[/api/stations/search]
        B --> F[/api/analyze]
        B --> G[/api/stations/all]
    end
    
    subgraph Business Logic
        E --> H[Station Search]
        F --> I[Route Analysis]
        G --> J[Station Listing]
    end
    
    subgraph Data Access
        H --> K[Network Graph]
        I --> K
        J --> K
        K --> L[(SQLite)]
    end
```

## UI Component Structure

```mermaid
graph TD
    ROOT[Root Container] --> HEADER[Header]
    ROOT --> MAIN[Main Layout]
    
    MAIN --> LEFT[Search Panel]
    MAIN --> CENTER[Map View]
    MAIN --> RIGHT[Results Panel]
    
    LEFT --> SEARCH_A[Station A Input]
    LEFT --> SEARCH_B[Station B Input]
    LEFT --> OPTIONS[Analysis Options]
    LEFT --> BUTTON[Analyze Button]
    
    CENTER --> MAP_CONTAINER[Leaflet Map]
    MAP_CONTAINER --> MARKERS[Station Markers]
    MAP_CONTAINER --> ROUTES[Route Polylines]
    MAP_CONTAINER --> CONTROLS[Map Controls]
    
    RIGHT --> FILTERS[Filter Controls]
    RIGHT --> LIST[Results List]
    RIGHT --> EXPORT[Export Options]
    
    LIST --> CARDS[Candidate Cards]
    CARDS --> DETAILS[Route Details Modal]
```

## Route Visualization States

```mermaid
stateDiagram-v2
    [*] --> Idle: Initial State
    
    Idle --> SearchingA: Select Work Station A
    SearchingA --> WaitingB: Station A Selected
    WaitingB --> Analyzing: Select Work Station B
    
    Analyzing --> Loading: Click Analyze
    Loading --> DisplayResults: Analysis Complete
    
    DisplayResults --> ShowingRoute: Select Candidate
    ShowingRoute --> DisplayResults: Deselect
    
    DisplayResults --> Comparing: Enable Compare Mode
    Comparing --> DisplayResults: Exit Compare
    
    DisplayResults --> Filtered: Apply Filters
    Filtered --> DisplayResults: Clear Filters
    
    ShowingRoute --> RouteDetails: View Details
    RouteDetails --> ShowingRoute: Close Details
    
    DisplayResults --> Idle: Reset
    ShowingRoute --> Idle: Reset
```

## Data Model - Key Entities

```mermaid
erDiagram
    STATION {
        string id PK
        string title
        string title_en
        float latitude
        float longitude
        string railway FK
        string operator
    }
    
    RAILWAY {
        string id PK
        string title
        string operator
        json station_order
        string color
    }
    
    ROUTE_SEGMENT {
        string from_station FK
        string to_station FK
        string railway FK
        float travel_time
        int num_stops
    }
    
    MEETING_POINT {
        string station_id FK
        float total_time
        float time_difference
        float balance_score
        json route_from_a
        json route_from_b
    }
    
    STATION ||--o{ ROUTE_SEGMENT : contains
    RAILWAY ||--o{ STATION : has
    STATION ||--o{ MEETING_POINT : is
    ROUTE_SEGMENT }o--|| RAILWAY : on
```

## Technology Stack

```mermaid
graph TB
    subgraph Frontend Stack
        HTML[HTML5] --> LEAF[Leaflet.js 1.9+]
        CSS[CSS3] --> GRID[CSS Grid/Flexbox]
        JS[JavaScript ES6+] --> FETCH[Fetch API]
    end
    
    subgraph Backend Stack
        PYTHON[Python 3.11+] --> FLASK[Flask 3.0+]
        FLASK --> CORS[Flask-CORS]
        FLASK --> JSON[JSON API]
    end
    
    subgraph Core Stack
        DIJKSTRA[Dijkstra Algorithm] --> HEAPQ[heapq]
        GRAPH[Network Graph] --> DICT[Dict/Set]
        SQLITE3[SQLite3] --> DB_API[DB-API 2.0]
    end
    
    JS --> JSON
    JSON --> PYTHON
    PYTHON --> DIJKSTRA
    DIJKSTRA --> SQLITE3
```

## Deployment Architecture

```mermaid
graph TB
    subgraph Production
        NGINX[Nginx Reverse Proxy] --> GUNICORN[Gunicorn Workers]
        GUNICORN --> FLASK1[Flask Instance 1]
        GUNICORN --> FLASK2[Flask Instance 2]
        GUNICORN --> FLASK3[Flask Instance 3]
    end
    
    subgraph Application
        FLASK1 --> CACHE[Redis Cache]
        FLASK2 --> CACHE
        FLASK3 --> CACHE
        CACHE --> DB[(PostgreSQL)]
    end
    
    subgraph Static Assets
        NGINX --> CDN[CDN for JS/CSS]
        CDN --> ASSETS[Static Files]
    end
    
    CLIENT[Clients] --> NGINX