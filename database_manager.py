"""Database manager for storing and querying train data in SQLite."""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class TrainDatabaseManager:
    """Manager for SQLite database operations."""
    
    def __init__(self, db_path: str = "train_data.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self) -> None:
        """Establish connection to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def create_schema(self) -> None:
        """Create database schema for all datasets."""
        
        # Trains table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trains (
                id TEXT PRIMARY KEY,
                context TEXT,
                type TEXT,
                date TEXT,
                valid TEXT,
                railway TEXT,
                train_number TEXT,
                train_type TEXT,
                rail_direction TEXT,
                operator TEXT,
                from_station TEXT,
                to_station TEXT,
                delay INTEGER,
                car_composition INTEGER,
                destination_stations TEXT,
                same_as TEXT,
                created_at TEXT
            )
        """)
        
        # Railways table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS railways (
                id TEXT PRIMARY KEY,
                context TEXT,
                type TEXT,
                title TEXT,
                title_en TEXT,
                operator TEXT,
                line_code TEXT,
                color TEXT,
                ascending_direction TEXT,
                descending_direction TEXT,
                station_order TEXT,
                same_as TEXT,
                created_at TEXT
            )
        """)
        
        # Stations table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                id TEXT PRIMARY KEY,
                context TEXT,
                type TEXT,
                title TEXT,
                title_en TEXT,
                railway TEXT,
                operator TEXT,
                station_code TEXT,
                latitude REAL,
                longitude REAL,
                region TEXT,
                exit_info TEXT,
                same_as TEXT,
                created_at TEXT
            )
        """)
        
        # Station timetables table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS station_timetables (
                id TEXT PRIMARY KEY,
                context TEXT,
                type TEXT,
                station TEXT,
                railway TEXT,
                operator TEXT,
                rail_direction TEXT,
                calendar TEXT,
                timetable_objects TEXT,
                same_as TEXT,
                created_at TEXT
            )
        """)
        
        # Train timetables table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS train_timetables (
                id TEXT PRIMARY KEY,
                context TEXT,
                type TEXT,
                train_number TEXT,
                train_type TEXT,
                railway TEXT,
                operator TEXT,
                rail_direction TEXT,
                calendar TEXT,
                origin_station TEXT,
                destination_station TEXT,
                via_railway TEXT,
                via_station TEXT,
                timetable_objects TEXT,
                note TEXT,
                same_as TEXT,
                created_at TEXT
            )
        """)
        
        # Create indexes for faster queries
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_trains_railway ON trains(railway)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_trains_train_number ON trains(train_number)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_trains_delay ON trains(delay)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_stations_railway ON stations(railway)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_station_timetables_station ON station_timetables(station)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_train_timetables_railway ON train_timetables(railway)")
        
        self.conn.commit()
    
    def clear_all_data(self) -> None:
        """Clear all data from all tables."""
        tables = ['trains', 'railways', 'stations', 'station_timetables', 'train_timetables']
        for table in tables:
            self.cursor.execute(f"DELETE FROM {table}")
        self.conn.commit()
    
    def insert_trains(self, trains: List[Dict[str, Any]]) -> int:
        """Insert train data into the database."""
        created_at = datetime.now().isoformat()
        count = 0
        
        for train in trains:
            # Handle destination stations (list)
            dest_stations = json.dumps(train.get("odpt:destinationStation", []))
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO trains 
                (id, context, type, date, valid, railway, train_number, train_type, 
                 rail_direction, operator, from_station, to_station, delay, 
                 car_composition, destination_stations, same_as, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                train.get("@id"),
                train.get("@context"),
                train.get("@type"),
                train.get("dc:date"),
                train.get("dct:valid"),
                train.get("odpt:railway"),
                train.get("odpt:trainNumber"),
                train.get("odpt:trainType"),
                train.get("odpt:railDirection"),
                train.get("odpt:operator"),
                train.get("odpt:fromStation"),
                train.get("odpt:toStation"),
                train.get("odpt:delay"),
                train.get("odpt:carComposition"),
                dest_stations,
                train.get("owl:sameAs"),
                created_at
            ))
            count += 1
        
        self.conn.commit()
        return count
    
    def insert_railways(self, railways: List[Dict[str, Any]]) -> int:
        """Insert railway data into the database."""
        created_at = datetime.now().isoformat()
        count = 0
        
        for railway in railways:
            # Handle station order (list)
            station_order = json.dumps(railway.get("odpt:stationOrder", []))
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO railways 
                (id, context, type, title, title_en, operator, line_code, color, 
                 ascending_direction, descending_direction, station_order, same_as, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                railway.get("@id"),
                railway.get("@context"),
                railway.get("@type"),
                railway.get("dc:title"),
                railway.get("odpt:railwayTitle", {}).get("en") if isinstance(railway.get("odpt:railwayTitle"), dict) else None,
                railway.get("odpt:operator"),
                railway.get("odpt:lineCode"),
                railway.get("odpt:color"),
                railway.get("odpt:ascendingRailDirection"),
                railway.get("odpt:descendingRailDirection"),
                station_order,
                railway.get("owl:sameAs"),
                created_at
            ))
            count += 1
        
        self.conn.commit()
        return count
    
    def insert_stations(self, stations: List[Dict[str, Any]]) -> int:
        """Insert station data into the database."""
        created_at = datetime.now().isoformat()
        count = 0
        
        for station in stations:
            # Handle exit info (complex object)
            exit_info = json.dumps(station.get("odpt:exit", []))
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO stations 
                (id, context, type, title, title_en, railway, operator, station_code, 
                 latitude, longitude, region, exit_info, same_as, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                station.get("@id"),
                station.get("@context"),
                station.get("@type"),
                station.get("dc:title"),
                station.get("odpt:stationTitle", {}).get("en") if isinstance(station.get("odpt:stationTitle"), dict) else None,
                station.get("odpt:railway"),
                station.get("odpt:operator"),
                station.get("odpt:stationCode"),
                station.get("geo:lat"),
                station.get("geo:long"),
                station.get("ug:region"),
                exit_info,
                station.get("owl:sameAs"),
                created_at
            ))
            count += 1
        
        self.conn.commit()
        return count
    
    def insert_station_timetables(self, timetables: List[Dict[str, Any]]) -> int:
        """Insert station timetable data into the database."""
        created_at = datetime.now().isoformat()
        count = 0
        
        for timetable in timetables:
            # Handle timetable objects (complex list)
            timetable_objects = json.dumps(timetable.get("odpt:stationTimetableObject", []))
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO station_timetables 
                (id, context, type, station, railway, operator, rail_direction, 
                 calendar, timetable_objects, same_as, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timetable.get("@id"),
                timetable.get("@context"),
                timetable.get("@type"),
                timetable.get("odpt:station"),
                timetable.get("odpt:railway"),
                timetable.get("odpt:operator"),
                timetable.get("odpt:railDirection"),
                timetable.get("odpt:calendar"),
                timetable_objects,
                timetable.get("owl:sameAs"),
                created_at
            ))
            count += 1
        
        self.conn.commit()
        return count
    
    def insert_train_timetables(self, timetables: List[Dict[str, Any]]) -> int:
        """Insert train timetable data into the database."""
        created_at = datetime.now().isoformat()
        count = 0
        
        for timetable in timetables:
            # Handle timetable objects (complex list)
            timetable_objects = json.dumps(timetable.get("odpt:trainTimetableObject", []))
            
            # Handle via railway and station (can be lists)
            via_railway = json.dumps(timetable.get("odpt:viaRailway", []))
            via_station = json.dumps(timetable.get("odpt:viaStation", []))
            
            # Handle origin and destination stations (can be lists or strings)
            origin_station = timetable.get("odpt:originStation")
            if isinstance(origin_station, list):
                origin_station = json.dumps(origin_station)
            
            destination_station = timetable.get("odpt:destinationStation")
            if isinstance(destination_station, list):
                destination_station = json.dumps(destination_station)
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO train_timetables
                (id, context, type, train_number, train_type, railway, operator,
                 rail_direction, calendar, origin_station, destination_station,
                 via_railway, via_station, timetable_objects, note, same_as, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timetable.get("@id"),
                timetable.get("@context"),
                timetable.get("@type"),
                timetable.get("odpt:trainNumber"),
                timetable.get("odpt:trainType"),
                timetable.get("odpt:railway"),
                timetable.get("odpt:operator"),
                timetable.get("odpt:railDirection"),
                timetable.get("odpt:calendar"),
                origin_station,
                destination_station,
                via_railway,
                via_station,
                timetable_objects,
                timetable.get("odpt:note"),
                timetable.get("owl:sameAs"),
                created_at
            ))
            count += 1
        
        self.conn.commit()
        return count
    
    def get_train_count(self) -> int:
        """Get total number of trains in database."""
        self.cursor.execute("SELECT COUNT(*) FROM trains")
        return self.cursor.fetchone()[0]
    
    def get_delayed_trains(self, min_delay: int = 60) -> List[Dict[str, Any]]:
        """Get trains with delays greater than specified seconds."""
        self.cursor.execute("""
            SELECT railway, train_number, delay, from_station, to_station 
            FROM trains 
            WHERE delay >= ? 
            ORDER BY delay DESC
        """, (min_delay,))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                "railway": row[0],
                "train_number": row[1],
                "delay": row[2],
                "from_station": row[3],
                "to_station": row[4]
            })
        return results
    
    def get_railway_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for each railway line."""
        self.cursor.execute("""
            SELECT 
                railway,
                COUNT(*) as train_count,
                AVG(delay) as avg_delay,
                MAX(delay) as max_delay,
                SUM(CASE WHEN delay > 0 THEN 1 ELSE 0 END) as delayed_count
            FROM trains 
            WHERE railway IS NOT NULL
            GROUP BY railway
            ORDER BY train_count DESC
        """)
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                "railway": row[0],
                "train_count": row[1],
                "avg_delay": round(row[2], 2),
                "max_delay": row[3],
                "delayed_count": row[4],
                "delay_rate": round((row[4] / row[1] * 100), 2) if row[1] > 0 else 0
            })
        return results
    
    def get_stations_by_railway(self, railway: str) -> List[Dict[str, Any]]:
        """Get all stations for a specific railway."""
        self.cursor.execute("""
            SELECT id, title, title_en, station_code, latitude, longitude
            FROM stations 
            WHERE railway = ?
            ORDER BY station_code
        """, (railway,))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "title": row[1],
                "title_en": row[2],
                "station_code": row[3],
                "latitude": row[4],
                "longitude": row[5]
            })
        return results
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()