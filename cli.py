"""Command-line interface for the train commute optimizer."""

import argparse
import sys
from typing import Optional, List
import config
from data_fetcher import DataFetcher
from commute_optimizer import CommuteOptimizer
from database_manager import TrainDatabaseManager


def cmd_fetch(args):
    """Execute the fetch command to populate the database."""
    fetcher = DataFetcher(args.db_path)
    
    # Determine which operators to fetch
    if args.operators:
        operator_keys = [op.strip().upper() for op in args.operators.split(",")]
        # Validate operator keys
        invalid = [op for op in operator_keys if op not in config.OPERATORS]
        if invalid:
            print(f"Error: Unknown operators: {', '.join(invalid)}")
            print(f"Valid operators: {', '.join(config.OPERATORS.keys())}")
            return 1
    else:
        operator_keys = None  # Fetch all
    
    try:
        stats = fetcher.fetch_and_populate(operator_keys)
        print("\n✓ Database updated successfully!")
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


def cmd_analyze(args):
    """Execute the analyze command to find optimal stations."""
    optimizer = CommuteOptimizer(args.db_path)
    
    # Search for stations by name
    print(f"\nSearching for stations...")
    
    # Load station info first
    optimizer.build_network()
    
    # Search for station A
    results_a = optimizer.search_station(args.station_a)
    if not results_a:
        print(f"✗ No stations found matching '{args.station_a}'")
        return 1
    
    # Search for station B
    results_b = optimizer.search_station(args.station_b)
    if not results_b:
        print(f"✗ No stations found matching '{args.station_b}'")
        return 1
    
    # If multiple results, show options
    station_a_id = None
    if len(results_a) == 1:
        station_a_id = results_a[0][0]
        print(f"✓ Found station A: {results_a[0][1]} ({results_a[0][2]})")
    else:
        print(f"\nMultiple stations found for '{args.station_a}':")
        for i, (sid, title, title_en, railway) in enumerate(results_a, 1):
            railway_name = railway.split(":")[-1] if ":" in railway else railway
            print(f"  {i}. {title} ({title_en}) - {railway_name}")
        
        choice = input("\nSelect station A (enter number): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results_a):
                station_a_id = results_a[idx][0]
                print(f"✓ Selected: {results_a[idx][1]}")
            else:
                print("✗ Invalid selection")
                return 1
        except ValueError:
            print("✗ Invalid input")
            return 1
    
    station_b_id = None
    if len(results_b) == 1:
        station_b_id = results_b[0][0]
        print(f"✓ Found station B: {results_b[0][1]} ({results_b[0][2]})")
    else:
        print(f"\nMultiple stations found for '{args.station_b}':")
        for i, (sid, title, title_en, railway) in enumerate(results_b, 1):
            railway_name = railway.split(":")[-1] if ":" in railway else railway
            print(f"  {i}. {title} ({title_en}) - {railway_name}")
        
        choice = input("\nSelect station B (enter number): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results_b):
                station_b_id = results_b[idx][0]
                print(f"✓ Selected: {results_b[idx][1]}")
            else:
                print("✗ Invalid selection")
                return 1
        except ValueError:
            print("✗ Invalid input")
            return 1
    
    # Run analysis
    try:
        candidates = optimizer.find_optimal_stations(
            work_station_a=station_a_id,
            work_station_b=station_b_id,
            top_n=args.top,
            max_time=args.max_time
        )
        
        if not candidates:
            print("\n✗ No common reachable stations found!")
            print("\nThis might be because:")
            print("  • The stations are too far apart")
            print("  • No connecting routes exist in the data")
            print("  • Maximum travel time is too restrictive")
            return 1
        
        optimizer.display_results(station_a_id, station_b_id, candidates)
        
        print("\n" + "=" * config.DISPLAY_WIDTH)
        print(" ANALYSIS COMPLETE")
        print("=" * config.DISPLAY_WIDTH)
        print(f"\nThese stations offer the best balance between:")
        print(f"  • Minimum total commute time for both people")
        print(f"  • Equal commute times (fairness)")
        print(f"  • Good connectivity to both work locations")
        print(f"\nNote: Times estimated at {config.DEFAULT_AVG_TIME_PER_STOP} min/stop")
        print(f"      + {config.DEFAULT_TRANSFER_TIME} min/transfer\n")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_search(args):
    """Execute the search command to find stations."""
    optimizer = CommuteOptimizer(args.db_path)
    optimizer.build_network()
    
    results = optimizer.search_station(args.station_name)
    
    if not results:
        print(f"No stations found matching '{args.station_name}'")
        return 1
    
    print(f"\nFound {len(results)} station(s):\n")
    for sid, title, title_en, railway in results:
        railway_name = railway.split(":")[-1] if ":" in railway else railway
        print(f"  {title} ({title_en})")
        print(f"    Railway: {railway_name}")
        print(f"    ID: {sid}\n")
    
    return 0


def cmd_stats(args):
    """Execute the stats command to show database statistics."""
    fetcher = DataFetcher(args.db_path)
    
    try:
        stats = fetcher.get_database_stats()
        
        print("\n" + "=" * config.DISPLAY_WIDTH)
        print(" DATABASE STATISTICS")
        print("=" * config.DISPLAY_WIDTH)
        print(f"\nStations: {stats['stations']}")
        print(f"Railways: {stats['railways']}")
        print(f"Railways with station order: {stats['railways_with_station_order']}")
        print(f"Operators: {stats['operators']}\n")
        
        return 0
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


def cmd_list_operators(args):
    """Execute the list-operators command."""
    print("\n" + "=" * config.DISPLAY_WIDTH)
    print(" AVAILABLE OPERATORS")
    print("=" * config.DISPLAY_WIDTH + "\n")
    
    for key, op_config in config.OPERATORS.items():
        print(f"{key}:")
        print(f"  Name: {op_config['name']}")
        print(f"  ID: {op_config['id']}")
        print(f"  API: {op_config['api_base']}\n")
    
    return 0


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Train Commute Optimizer - Find ideal living stations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch data from all operators
  python cli.py fetch
  
  # Fetch only from specific operators
  python cli.py fetch --operators JR_EAST,TOKYO_METRO
  
  # Analyze commute between two stations
  python cli.py analyze 六本木 海浜幕張
  python cli.py analyze Roppongi Kaihimmakuhari --top 10
  
  # Search for a station
  python cli.py search 渋谷
  
  # Show database statistics
  python cli.py stats
  
  # List available operators
  python cli.py list-operators
        """
    )
    
    parser.add_argument(
        "--db-path",
        default=config.DEFAULT_DB_PATH,
        help=f"Path to database file (default: {config.DEFAULT_DB_PATH})"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Fetch command
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch data from operators and populate database"
    )
    fetch_parser.add_argument(
        "--operators",
        help="Comma-separated list of operators (e.g., JR_EAST,TOKYO_METRO). Default: all"
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Find optimal living stations for dual commute"
    )
    analyze_parser.add_argument(
        "station_a",
        help="First work station (name or partial name)"
    )
    analyze_parser.add_argument(
        "station_b",
        help="Second work station (name or partial name)"
    )
    analyze_parser.add_argument(
        "--top",
        type=int,
        default=config.DEFAULT_TOP_N_RESULTS,
        help=f"Number of results to show (default: {config.DEFAULT_TOP_N_RESULTS})"
    )
    analyze_parser.add_argument(
        "--max-time",
        type=float,
        default=config.DEFAULT_MAX_COMMUTE_TIME,
        help=f"Maximum commute time in minutes (default: {config.DEFAULT_MAX_COMMUTE_TIME})"
    )
    
    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search for stations by name"
    )
    search_parser.add_argument(
        "station_name",
        help="Station name or partial name to search for"
    )
    
    # Stats command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show database statistics"
    )
    
    # List operators command
    list_ops_parser = subparsers.add_parser(
        "list-operators",
        help="List available operators"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == "fetch":
        return cmd_fetch(args)
    elif args.command == "analyze":
        return cmd_analyze(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "stats":
        return cmd_stats(args)
    elif args.command == "list-operators":
        return cmd_list_operators(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())