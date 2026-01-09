"""Data fetcher for train network data from ODPT APIs."""

import os
import requests
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import config
from database_manager import TrainDatabaseManager


class DataFetcher:
    """Fetches train network data from multiple operators and populates database."""
    
    def __init__(self, db_path: str = config.DEFAULT_DB_PATH):
        """
        Initialize the data fetcher.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        load_dotenv()
    
    def _get_api_url(self, api_base: str) -> str:
        """Get the appropriate API base URL."""
        if api_base == "production":
            return config.ODPT_API_BASE_URL
        else:
            return config.ODPT_API_CHALLENGE_BASE_URL
    
    def _fetch_data(
        self,
        resource_type: str,
        operator_id: str,
        api_base: str,
        env_key: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from the ODPT API.
        
        Args:
            resource_type: Type of resource (e.g., 'Station', 'Railway')
            operator_id: Operator identifier
            api_base: Which API to use ('production' or 'challenge')
            env_key: Environment variable name for API key
            
        Returns:
            List of data dictionaries
            
        Raises:
            requests.RequestException: If the API request fails
        """
        base_url = self._get_api_url(api_base)
        endpoint = f"{base_url}/odpt:{resource_type}"
        
        # Get API key from environment
        api_key = os.getenv(env_key)
        if not api_key:
            raise ValueError(f"{env_key} not found in environment variables")
        
        params = {
            "odpt:operator": operator_id,
            "acl:consumerKey": api_key
        }
        
        print(f"    Fetching {resource_type}...")
        response = requests.get(endpoint, params=params, timeout=config.API_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        print(f"    ✓ Fetched {len(data)} {resource_type} records")
        return data
    
    def fetch_operator_data(self, operator_key: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch all data for a specific operator.
        
        Args:
            operator_key: Key from config.OPERATORS (e.g., 'JR_EAST')
            
        Returns:
            Dictionary with 'stations' and 'railways' data
        """
        if operator_key not in config.OPERATORS:
            raise ValueError(f"Unknown operator: {operator_key}")
        
        operator_config = config.OPERATORS[operator_key]
        operator_id = operator_config["id"]
        api_base = operator_config["api_base"]
        env_key = operator_config["env_key"]
        
        print(f"\n--- Fetching {operator_config['name']} data ---")
        
        try:
            stations = self._fetch_data("Station", operator_id, api_base, env_key)
            railways = self._fetch_data("Railway", operator_id, api_base, env_key)
            
            return {
                "stations": stations,
                "railways": railways
            }
        except Exception as e:
            print(f"    ✗ Error fetching {operator_config['name']}: {e}")
            return {
                "stations": [],
                "railways": []
            }
    
    def fetch_all_operators(
        self,
        operator_keys: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Fetch data from all specified operators.
        
        Args:
            operator_keys: List of operator keys to fetch, or None for all
            
        Returns:
            Dictionary mapping operator keys to their data
        """
        if operator_keys is None:
            operator_keys = list(config.OPERATORS.keys())
        
        print("\n" + "=" * config.DISPLAY_WIDTH)
        print(" FETCHING DATA FROM MULTIPLE OPERATORS")
        print("=" * config.DISPLAY_WIDTH)
        
        all_data = {}
        for operator_key in operator_keys:
            all_data[operator_key] = self.fetch_operator_data(operator_key)
        
        print("\n" + "=" * config.DISPLAY_WIDTH)
        print(" DATA FETCHING COMPLETE")
        print("=" * config.DISPLAY_WIDTH)
        
        return all_data
    
    def populate_database(
        self,
        data: Dict[str, Dict[str, List[Dict[str, Any]]]]
    ) -> Dict[str, int]:
        """
        Populate the database with fetched data.
        
        Args:
            data: Dictionary mapping operator keys to their data
            
        Returns:
            Dictionary with statistics about inserted records
        """
        print("\n" + "=" * config.DISPLAY_WIDTH)
        print(" POPULATING DATABASE")
        print("=" * config.DISPLAY_WIDTH)
        
        stats = {
            "stations": 0,
            "railways": 0
        }
        
        with TrainDatabaseManager(self.db_path) as db:
            db.create_schema()
            db.clear_all_data()
            
            for operator_key, operator_data in data.items():
                operator_name = config.OPERATORS[operator_key]["name"]
                
                if operator_data["stations"]:
                    print(f"\nStoring {operator_name} stations...")
                    count = db.insert_stations(operator_data["stations"])
                    stats["stations"] += count
                    print(f"  ✓ Stored {count} stations")
                
                if operator_data["railways"]:
                    print(f"Storing {operator_name} railways...")
                    count = db.insert_railways(operator_data["railways"])
                    stats["railways"] += count
                    print(f"  ✓ Stored {count} railways")
        
        print("\n" + "=" * config.DISPLAY_WIDTH)
        print(" DATABASE POPULATION COMPLETE")
        print("=" * config.DISPLAY_WIDTH)
        print(f"\nTotal stations: {stats['stations']}")
        print(f"Total railways: {stats['railways']}\n")
        
        return stats
    
    def fetch_and_populate(
        self,
        operator_keys: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Fetch data from operators and populate database in one operation.
        
        Args:
            operator_keys: List of operator keys to fetch, or None for all
            
        Returns:
            Dictionary with statistics about inserted records
        """
        data = self.fetch_all_operators(operator_keys)
        stats = self.populate_database(data)
        return stats
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current database contents.
        
        Returns:
            Dictionary with database statistics
        """
        with TrainDatabaseManager(self.db_path) as db:
            db.cursor.execute("SELECT COUNT(*) FROM stations")
            station_count = db.cursor.fetchone()[0]
            
            db.cursor.execute("SELECT COUNT(*) FROM railways")
            railway_count = db.cursor.fetchone()[0]
            
            db.cursor.execute("""
                SELECT COUNT(*) FROM railways 
                WHERE station_order IS NOT NULL AND station_order != '[]'
            """)
            railways_with_order = db.cursor.fetchone()[0]
            
            db.cursor.execute("SELECT COUNT(DISTINCT operator) FROM stations")
            operator_count = db.cursor.fetchone()[0]
            
            return {
                "stations": station_count,
                "railways": railway_count,
                "railways_with_station_order": railways_with_order,
                "operators": operator_count
            }


def main():
    """Example usage of the data fetcher."""
    fetcher = DataFetcher()
    
    # Fetch from all operators and populate database
    stats = fetcher.fetch_and_populate()
    
    print("\nDatabase populated successfully!")
    print(f"  Stations: {stats['stations']}")
    print(f"  Railways: {stats['railways']}")


if __name__ == "__main__":
    main()