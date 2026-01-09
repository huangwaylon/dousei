"""Commute optimizer for finding ideal living stations between two work locations."""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from heapq import heappush, heappop
from collections import defaultdict
import config
from database_manager import TrainDatabaseManager


@dataclass
class RouteSegment:
    """A segment of a route from one station to another."""
    from_station: str
    to_station: str
    railway: str
    travel_time: float
    num_stops: int


@dataclass
class Route:
    """Complete route from origin to destination."""
    segments: List[RouteSegment]
    total_time: float
    total_stops: int
    
    def get_transfer_count(self) -> int:
        """Count the number of transfers in this route."""
        if not self.segments:
            return 0
        
        transfers = 0
        for i in range(1, len(self.segments)):
            if self.segments[i].railway != self.segments[i-1].railway:
                transfers += 1
        return transfers


@dataclass
class MeetingPoint:
    """A candidate meeting point with routes from both origin stations."""
    station_id: str
    station_name: str
    route_from_a: Route
    route_from_b: Route
    total_time: float
    time_difference: float
    balance_score: float


class CommuteOptimizer:
    """Optimizer for finding ideal living stations for dual commute."""
    
    def __init__(self, db_path: str = config.DEFAULT_DB_PATH):
        """
        Initialize the optimizer with database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.network_graph = {}
        self.station_info = {}
        self.railway_info = {}
        self.transfer_stations = {}  # Maps station name to set of station IDs
    
    def build_network(self) -> None:
        """Build network graph from railway station order data."""
        print("\nBuilding network from railway station orders...")
        
        with TrainDatabaseManager(self.db_path) as db:
            # Get all stations
            db.cursor.execute("""
                SELECT same_as, title, title_en, railway, latitude, longitude
                FROM stations
                WHERE same_as IS NOT NULL
            """)
            
            for row in db.cursor.fetchall():
                station_id, title, title_en, railway, lat, lon = row
                self.station_info[station_id] = {
                    "title": title,
                    "title_en": title_en,
                    "railway": railway,
                    "latitude": lat,
                    "longitude": lon
                }
                
                # Build transfer station mapping
                if title not in self.transfer_stations:
                    self.transfer_stations[title] = set()
                self.transfer_stations[title].add(station_id)
            
            # Get railway information with station order
            db.cursor.execute("""
                SELECT same_as, title, title_en, station_order
                FROM railways
                WHERE same_as IS NOT NULL AND station_order IS NOT NULL
            """)
            
            railway_count = 0
            for row in db.cursor.fetchall():
                railway_id, title, title_en, station_order_json = row
                self.railway_info[railway_id] = {
                    "title": title,
                    "title_en": title_en
                }
                
                try:
                    station_order = json.loads(station_order_json)
                    if station_order:  # Only process if not empty
                        self._process_railway_order(railway_id, station_order)
                        railway_count += 1
                except (json.JSONDecodeError, KeyError):
                    continue
            
            print(f"  ✓ Processed {railway_count} railway lines")
            print(f"  ✓ Built graph with {len(self.network_graph)} stations")
            print(f"  ✓ Found {len(self.transfer_stations)} station names")
            
            # Add transfer connections
            self._add_transfer_connections()
    
    def _process_railway_order(self, railway: str, station_order: List[Dict]) -> None:
        """Process railway station order to build network connections."""
        for i in range(len(station_order) - 1):
            current = station_order[i]
            next_stop = station_order[i + 1]
            
            current_station = current.get("odpt:station")
            next_station = next_stop.get("odpt:station")
            
            if not current_station or not next_station:
                continue
            
            # Use configured travel time
            travel_time = config.DEFAULT_AVG_TIME_PER_STOP
            
            # Add bidirectional connections
            if current_station not in self.network_graph:
                self.network_graph[current_station] = []
            
            self.network_graph[current_station].append({
                "to_station": next_station,
                "travel_time": travel_time,
                "railway": railway,
                "num_stops": 1
            })
            
            if next_station not in self.network_graph:
                self.network_graph[next_station] = []
            
            self.network_graph[next_station].append({
                "to_station": current_station,
                "travel_time": travel_time,
                "railway": railway,
                "num_stops": 1
            })
    
    def _add_transfer_connections(self) -> None:
        """Add transfer connections between stations with the same name."""
        transfer_count = 0
        for station_name, station_ids in self.transfer_stations.items():
            if len(station_ids) > 1:
                # Create connections between all stations with same name
                station_list = list(station_ids)
                for i in range(len(station_list)):
                    for j in range(i + 1, len(station_list)):
                        station_a = station_list[i]
                        station_b = station_list[j]
                        
                        # Add bidirectional transfer
                        if station_a in self.network_graph:
                            self.network_graph[station_a].append({
                                "to_station": station_b,
                                "travel_time": config.DEFAULT_TRANSFER_TIME,
                                "railway": "Transfer",
                                "num_stops": 0
                            })
                        
                        if station_b in self.network_graph:
                            self.network_graph[station_b].append({
                                "to_station": station_a,
                                "travel_time": config.DEFAULT_TRANSFER_TIME,
                                "railway": "Transfer",
                                "num_stops": 0
                            })
                        
                        transfer_count += 1
        
        print(f"  ✓ Added {transfer_count} transfer connections")
    
    def _dijkstra_with_path(
        self,
        start_station: str,
        max_time: float = config.DEFAULT_MAX_COMMUTE_TIME
    ) -> Dict[str, Tuple[float, Route]]:
        """
        Run Dijkstra's algorithm and track the actual routes.
        
        Args:
            start_station: Starting station ID
            max_time: Maximum travel time to consider (in minutes)
            
        Returns:
            Dictionary mapping station_id to (travel_time, Route)
        """
        distances = {start_station: (0, Route([], 0, 0))}
        pq = [(0, start_station, [])]  # (time, station, path_segments)
        visited = set()
        
        while pq:
            current_time, current_station, path_segments = heappop(pq)
            
            if current_station in visited:
                continue
            
            visited.add(current_station)
            
            if current_time > max_time:
                continue
            
            if current_station not in self.network_graph:
                continue
            
            for connection in self.network_graph[current_station]:
                next_station = connection["to_station"]
                travel_time = connection["travel_time"]
                railway = connection["railway"]
                num_stops = connection["num_stops"]
                
                new_time = current_time + travel_time
                
                if new_time <= max_time:
                    segment = RouteSegment(
                        from_station=current_station,
                        to_station=next_station,
                        railway=railway,
                        travel_time=travel_time,
                        num_stops=num_stops
                    )
                    
                    new_path = path_segments + [segment]
                    new_route = Route(
                        segments=new_path,
                        total_time=new_time,
                        total_stops=sum(seg.num_stops for seg in new_path)
                    )
                    
                    if next_station not in distances or new_time < distances[next_station][0]:
                        distances[next_station] = (new_time, new_route)
                        heappush(pq, (new_time, next_station, new_path))
        
        return distances
    
    def find_optimal_stations(
        self,
        work_station_a: str,
        work_station_b: str,
        top_n: int = config.DEFAULT_TOP_N_RESULTS,
        max_time: float = config.DEFAULT_MAX_COMMUTE_TIME
    ) -> List[MeetingPoint]:
        """
        Find optimal living stations for two people working at different locations.
        
        Args:
            work_station_a: Station ID for person A's workplace
            work_station_b: Station ID for person B's workplace
            top_n: Number of top results to return
            max_time: Maximum commute time to consider (minutes)
            
        Returns:
            List of MeetingPoint candidates, sorted by total time and balance
        """
        if not self.network_graph:
            self.build_network()
        
        work_a_name = self.station_info.get(work_station_a, {}).get('title', work_station_a)
        work_b_name = self.station_info.get(work_station_b, {}).get('title', work_station_b)
        
        print(f"\nCalculating routes from {work_a_name}...")
        routes_from_a = self._dijkstra_with_path(work_station_a, max_time)
        print(f"  ✓ Found {len(routes_from_a)} reachable stations")
        
        print(f"Calculating routes from {work_b_name}...")
        routes_from_b = self._dijkstra_with_path(work_station_b, max_time)
        print(f"  ✓ Found {len(routes_from_b)} reachable stations")
        
        # Find common stations
        common_stations = set(routes_from_a.keys()) & set(routes_from_b.keys())
        common_stations.discard(work_station_a)
        common_stations.discard(work_station_b)
        
        print(f"  ✓ Found {len(common_stations)} common reachable stations\n")
        
        # Create meeting point candidates
        candidates = []
        for station in common_stations:
            time_a, route_a = routes_from_a[station]
            time_b, route_b = routes_from_b[station]
            
            total_time = time_a + time_b
            time_diff = abs(time_a - time_b)
            
            # Balance score: 1.0 = perfect balance, 0.0 = maximum imbalance
            balance_score = 1 - (time_diff / max_time)
            
            station_name = self.station_info.get(station, {}).get("title", "Unknown")
            
            candidates.append(MeetingPoint(
                station_id=station,
                station_name=station_name,
                route_from_a=route_a,
                route_from_b=route_b,
                total_time=total_time,
                time_difference=time_diff,
                balance_score=balance_score
            ))
        
        # Sort by: 1) minimum total time, 2) best balance
        candidates.sort(key=lambda x: (x.total_time, x.time_difference))
        
        return candidates[:top_n]
    
    def display_results(
        self,
        work_station_a: str,
        work_station_b: str,
        candidates: List[MeetingPoint]
    ) -> None:
        """Display search results with detailed route information."""
        print("\n" + "=" * config.DISPLAY_WIDTH)
        print(" OPTIMAL LIVING STATION FINDER")
        print("=" * config.DISPLAY_WIDTH)
        
        work_a_name = self.station_info.get(work_station_a, {}).get("title", work_station_a)
        work_b_name = self.station_info.get(work_station_b, {}).get("title", work_station_b)
        
        print(f"\nPerson A works at: {work_a_name}")
        print(f"Person B works at: {work_b_name}")
        print(f"\nTop {len(candidates)} stations (ordered by min total time & equal commute):\n")
        
        for i, candidate in enumerate(candidates, 1):
            print("=" * config.DISPLAY_WIDTH)
            print(f"#{i} {candidate.station_name}")
            print("=" * config.DISPLAY_WIDTH)
            print(f"Total commute time: {candidate.total_time:.1f} minutes")
            print(f"Time difference: {candidate.time_difference:.1f} minutes")
            print(f"Balance score: {candidate.balance_score:.3f}\n")
            
            # Person A's commute
            print(f"Person A's commute to {work_a_name}: {candidate.route_from_a.total_time:.1f} minutes")
            self._display_route(candidate.route_from_a)
            
            print()
            
            # Person B's commute
            print(f"Person B's commute to {work_b_name}: {candidate.route_from_b.total_time:.1f} minutes")
            self._display_route(candidate.route_from_b)
            
            print()
    
    def _display_route(self, route: Route) -> None:
        """Display a single route with transfer information."""
        if not route.segments:
            print("  Direct connection (already at destination)")
            return
        
        transfers = route.get_transfer_count()
        print(f"  Transfers: {transfers}")
        print(f"  Total stops: {route.total_stops}\n")
        
        current_railway = None
        segment_group = []
        
        for segment in route.segments:
            if segment.railway == "Transfer":
                # Display previous group if exists
                if segment_group:
                    self._display_segment_group(segment_group, current_railway)
                    segment_group = []
                
                # Display transfer
                from_name = self.station_info.get(segment.from_station, {}).get("title", "Unknown")
                print(f"  Transfer at {from_name} ({segment.travel_time:.1f} min)\n")
                current_railway = None
                
            elif segment.railway != current_railway:
                # Display previous group if exists
                if segment_group:
                    self._display_segment_group(segment_group, current_railway)
                    print()
                
                current_railway = segment.railway
                segment_group = [segment]
            else:
                segment_group.append(segment)
        
        # Display last group
        if segment_group:
            self._display_segment_group(segment_group, current_railway)
    
    def _display_segment_group(self, segments: List[RouteSegment], railway: str) -> None:
        """Display a group of segments on the same railway line."""
        railway_info = self.railway_info.get(railway, {})
        railway_name = railway_info.get("title", railway.split(":")[-1] if ":" in railway else railway)
        
        from_station = self.station_info.get(segments[0].from_station, {}).get("title", "Unknown")
        to_station = self.station_info.get(segments[-1].to_station, {}).get("title", "Unknown")
        
        total_time = sum(seg.travel_time for seg in segments)
        total_stops = sum(seg.num_stops for seg in segments)
        
        print(f"  [{railway_name}]")
        print(f"    {from_station} → {to_station}")
        print(f"    ({total_stops} stops, {total_time:.1f} minutes)")
    
    def search_station(self, search_term: str) -> List[Tuple[str, str, str, str]]:
        """
        Search for stations by name.
        
        Args:
            search_term: Search term (case-insensitive)
            
        Returns:
            List of tuples: (station_id, title, title_en, railway)
        """
        search_term_lower = search_term.lower()
        results = []
        
        for station_id, info in self.station_info.items():
            title = info.get("title", "")
            title_en = info.get("title_en", "")
            railway = info.get("railway", "")
            
            if (search_term_lower in title.lower() or
                search_term_lower in title_en.lower()):
                results.append((station_id, title, title_en, railway))
        
        return sorted(results, key=lambda x: x[1])


def main():
    """Example usage of the commute optimizer."""
    optimizer = CommuteOptimizer()
    
    # Example: Find ideal stations for Roppongi and Kaihin Makuhari
    work_station_a = "odpt.Station:TokyoMetro.Hibiya.Roppongi"
    work_station_b = "odpt.Station:JR-East.Keiyo.Kaihimmakuhari"
    
    candidates = optimizer.find_optimal_stations(
        work_station_a=work_station_a,
        work_station_b=work_station_b,
        top_n=10
    )
    
    optimizer.display_results(work_station_a, work_station_b, candidates)


if __name__ == "__main__":
    main()