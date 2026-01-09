# Train Commute Optimizer

A production-ready application for finding ideal living stations for dual commute scenarios in Japan's train network. Supports JR East, Tokyo Metro, and Keikyu rail operators.

## Features

- **Part 1: Data Fetching** - Fetch and populate train network data from multiple operators
- **Part 2: Commute Analysis** - Find optimal living stations that balance two commutes
- **Multi-operator Support** - JR East, Tokyo Metro, and Keikyu networks
- **Transfer Optimization** - Automatically considers transfers between lines and operators
- **Balance Scoring** - Ranks stations by total time and fairness between commuters

## Architecture

```
trains/
├── config.py              # Configuration and constants
├── data_fetcher.py        # Part 1: Data acquisition
├── commute_optimizer.py   # Part 2: Commute analysis engine  
├── database_manager.py    # SQLite database operations
├── cli.py                 # Command-line interface
├── .env                   # API keys (create this)
├── train_data.db          # SQLite database (generated)
└── README.md             # This file
```

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Create `.env` File

Create a `.env` file in the project root with your API keys:

```
ACCESS_TOKEN=your_jreast_keikyu_token_here
TOKYO_METRO_KEY=your_tokyo_metro_token_here
```

**API Keys:**
- `ACCESS_TOKEN` - Used for JR East and Keikyu (challenge API)
- `TOKYO_METRO_KEY` - Used for Tokyo Metro (production API)

Both keys are loaded from the `.env` file for security best practices.

## Usage

### Part 1: Fetch and Populate Data

Fetch train network data from all operators:

```bash
python cli.py fetch
```

Fetch from specific operators only:

```bash
python cli.py fetch --operators JR_EAST,TOKYO_METRO
```

This will:
- Fetch stations and railway data from APIs
- Populate the SQLite database
- Build network graph for analysis

Expected output:
```
Fetched 1150 stations across 3 operators
Stored 103 railway lines
```

### Part 2: Run Commute Analysis

Find optimal living stations for two work locations:

```bash
python cli.py analyze 六本木 海浜幕張
python cli.py analyze Roppongi Kaihimmakuhari --top 10
```

Options:
- `--top N` - Show top N results (default: 10)
- `--max-time MINUTES` - Maximum commute time (default: 120)

The analysis will:
1. Search for matching stations
2. Build network graph
3. Calculate routes from both work locations
4. Find common reachable stations
5. Rank by total time and balance

### Utility Commands

**Search for stations:**
```bash
python cli.py search 渋谷
python cli.py search Shibuya
```

**Show database statistics:**
```bash
python cli.py stats
```

**List available operators:**
```bash
python cli.py list-operators
```

## Example: Finding Ideal Station

```bash
# Fetch data (once)
python cli.py fetch

# Find stations for Roppongi and Kaihin Makuhari
python cli.py analyze 六本木 海浜幕張 --top 5
```

Output will show:
- Top 5 stations ranked by minimum total commute time
- Detailed routes for each person
- Transfer information
- Balance scores

Example result:
```
#1 潮見 (Shiomi)
Total commute time: 57.5 minutes
Time difference: 2.5 minutes (excellent balance!)
Balance score: 0.979

Person A → Roppongi: 30.0 min (Hibiya Line → Transfer → Keiyo Line)
Person B → Kaihin Makuhari: 27.5 min (Direct Keiyo Line)
```

## Configuration

All configuration is in [`config.py`](config.py:1):

```python
# Timing parameters
DEFAULT_AVG_TIME_PER_STOP = 2.5  # minutes per station
DEFAULT_TRANSFER_TIME = 5.0       # minutes per transfer
DEFAULT_MAX_COMMUTE_TIME = 120    # max commute time to consider

# Analysis parameters  
DEFAULT_TOP_N_RESULTS = 10        # number of results to show

# Operator configuration (API keys loaded from .env)
OPERATORS = {
    "JR_EAST": {
        "env_key": "ACCESS_TOKEN",
        ...
    },
    "TOKYO_METRO": {
        "env_key": "TOKYO_METRO_KEY",
        ...
    },
    ...
}
```

## How It Works

### Network Graph Building

1. Loads railway station orders from database
2. Creates bidirectional edges between consecutive stations
3. Adds transfer connections between stations with same name
4. Estimates travel time: 2.5 min/stop + 5 min/transfer

### Route Finding Algorithm

Uses Dijkstra's algorithm with path reconstruction:
1. Start from both work stations
2. Find all reachable stations within max time
3. Identify common reachable stations
4. Calculate total commute time and balance score
5. Rank by (total_time, time_difference)

### Balance Scoring

```
balance_score = 1 - (time_difference / max_time)
```

- 1.0 = perfect balance (equal commute times)
- 0.0 = maximum imbalance

## API Keys

All API keys are stored securely in the `.env` file:

### Tokyo Metro
- Uses production API (`api.odpt.org`)
- Key stored as `TOKYO_METRO_KEY` in `.env`

### JR East & Keikyu  
- Use challenge API (`api-challenge.odpt.org`)
- Key stored as `ACCESS_TOKEN` in `.env`

To get API keys:
1. Visit https://developer.odpt.org/
2. Register for an account
3. Generate access tokens
4. Add to `.env` file

**Example `.env` file:**
```
ACCESS_TOKEN=your_jreast_keikyu_token_here
TOKYO_METRO_KEY=your_tokyo_metro_token_here
```

## Database Schema

SQLite database with 2 main tables:

**stations:**
- Station identifiers and names
- GPS coordinates
- Railway and operator associations

**railways:**
- Railway line information
- Station order (JSON array)
- Line colors and codes

The station_order JSON defines the network topology for routing.

## Troubleshooting

**"ACCESS_TOKEN not found" or "TOKYO_METRO_KEY not found"**
- Create `.env` file with your API tokens
- Make sure it's in the project root directory
- Check that both keys are present

**"No common reachable stations found"**
- Stations may be too far apart
- Try increasing `--max-time`
- Ensure database is populated with all operators

**"Multiple stations found"**
- The CLI will prompt you to select which station
- Enter the number of your choice
- Or be more specific in your search term

## Development

### Project Structure

- [`config.py`](config.py:1) - All constants and configuration
- [`data_fetcher.py`](data_fetcher.py:1) - API client and data population
- [`commute_optimizer.py`](commute_optimizer.py:1) - Network graph and routing
- [`database_manager.py`](database_manager.py:1) - SQLite operations  
- [`cli.py`](cli.py:1) - Command-line interface

### Adding New Operators

1. Get API key for the operator
2. Add operator config to [`config.py`](config.py:11)
3. Add API key to `.env` file
4. Run `python cli.py fetch` to populate data

### Customizing Travel Times

Edit [`config.py`](config.py:30):
```python
DEFAULT_AVG_TIME_PER_STOP = 2.5  # Adjust per-stop time
DEFAULT_TRANSFER_TIME = 5.0       # Adjust transfer time
```

## Security

- ✅ All API keys stored in `.env` file (not in code)
- ✅ `.env` file in `.gitignore` (never committed)
- ✅ Keys loaded at runtime from environment
- ✅ No hardcoded secrets in codebase

## Performance

- **Data fetching**: ~30 seconds for all operators
- **Network building**: ~2 seconds for 1000+ stations
- **Route finding**: ~1-2 seconds per analysis
- **Database size**: ~35 MB with full network data

## License

This project uses public transportation data from the Open Data Challenge for Public Transportation in Tokyo (ODPT).

## Support

For issues or questions:
1. Check this README first
2. Review [`config.py`](config.py:1) settings
3. Try `python cli.py stats` to verify database
4. Verify API keys in `.env` file