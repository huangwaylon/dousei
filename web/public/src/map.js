/**
 * Map Controller for Leaflet.js
 * Handles all map interactions and visualizations
 */

export class MapController {
  constructor(elementId) {
    this.elementId = elementId;
    this.map = null;
    this.markers = {
      workA: null,
      workB: null,
      candidates: []
    };
    this.routeLayers = [];
    this.routesVisible = true;
  }

  /**
   * Initialize the map
   */
  init() {
    // Create map centered on Tokyo
    this.map = L.map(this.elementId, {
      zoomControl: true,
      scrollWheelZoom: true,
    }).setView([35.6762, 139.6503], 11);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
      minZoom: 9,
    }).addTo(this.map);

    // Add scale control
    L.control.scale({ imperial: false }).addTo(this.map);

    console.log('Map initialized');
  }

  /**
   * Add work station marker
   */
  addWorkStation(station, type) {
    const color = type === 'a' ? '#ef4444' : '#3b82f6';
    const label = type === 'a' ? 'A' : 'B';
    
    const icon = L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        background-color: ${color};
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 16px;
        border: 3px solid white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      ">${label}</div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    const marker = L.marker([station.latitude, station.longitude], {
      icon: icon,
      title: station.name,
    }).addTo(this.map);

    marker.bindPopup(`
      <div style="min-width: 200px;">
        <strong style="font-size: 1.1em;">Person ${label}'s Work</strong><br>
        <span style="font-size: 0.95em;">${station.name}</span>
      </div>
    `);

    if (type === 'a') {
      this.markers.workA = marker;
    } else {
      this.markers.workB = marker;
    }

    return marker;
  }

  /**
   * Add candidate station marker
   */
  addCandidateMarker(candidate, rank, isSelected = false) {
    const size = isSelected ? 36 : Math.max(28, 36 - rank * 2);
    const opacity = isSelected ? 1.0 : 0.7;
    
    const icon = L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        background-color: #10b981;
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: ${Math.floor(size * 0.5)}px;
        border: ${isSelected ? '4px' : '3px'} solid white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        opacity: ${opacity};
        transition: all 0.2s;
      ">${rank}</div>`,
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
    });

    const marker = L.marker([candidate.latitude, candidate.longitude], {
      icon: icon,
      title: `#${rank}: ${candidate.station_name}`,
      candidateId: candidate.station_id,
    }).addTo(this.map);

    marker.bindPopup(`
      <div style="min-width: 220px;">
        <strong style="font-size: 1.1em;">Rank #${rank}</strong><br>
        <span style="font-size: 1em; font-weight: 600;">${candidate.station_name}</span><br>
        <div style="margin-top: 8px; font-size: 0.9em; color: #666;">
          <div>⏱️ Total: ${candidate.total_time.toFixed(1)} min</div>
          <div>⚖️ Balance: ${(candidate.balance_score * 100).toFixed(0)}%</div>
        </div>
      </div>
    `);

    this.markers.candidates.push(marker);
    return marker;
  }

  /**
   * Draw a route on the map
   */
  drawRoute(segments, color, opacity = 0.7, weight = 4) {
    const coordinates = [];
    
    segments.forEach(segment => {
      if (!segment.is_transfer) {
        coordinates.push([segment.from_coordinates[0], segment.from_coordinates[1]]);
        coordinates.push([segment.to_coordinates[0], segment.to_coordinates[1]]);
      }
    });

    if (coordinates.length === 0) return null;

    const polyline = L.polyline(coordinates, {
      color: color,
      weight: weight,
      opacity: opacity,
      smoothFactor: 1,
    }).addTo(this.map);

    this.routeLayers.push(polyline);
    return polyline;
  }

  /**
   * Draw all routes for a candidate
   */
  drawCandidateRoutes(candidate, selected = false) {
    const opacity = selected ? 0.8 : 0.4;
    const weight = selected ? 5 : 3;

    // Draw route from A (red)
    this.drawRoute(
      candidate.route_from_a.segments,
      '#ef4444',
      opacity,
      weight
    );

    // Draw route from B (blue)
    this.drawRoute(
      candidate.route_from_b.segments,
      '#3b82f6',
      opacity,
      weight
    );
  }

  /**
   * Clear all route layers
   */
  clearRoutes() {
    this.routeLayers.forEach(layer => {
      this.map.removeLayer(layer);
    });
    this.routeLayers = [];
  }

  /**
   * Clear all candidate markers
   */
  clearCandidates() {
    this.markers.candidates.forEach(marker => {
      this.map.removeLayer(marker);
    });
    this.markers.candidates = [];
  }

  /**
   * Clear work station markers
   */
  clearWorkStations() {
    if (this.markers.workA) {
      this.map.removeLayer(this.markers.workA);
      this.markers.workA = null;
    }
    if (this.markers.workB) {
      this.map.removeLayer(this.markers.workB);
      this.markers.workB = null;
    }
  }

  /**
   * Clear everything
   */
  clearAll() {
    this.clearRoutes();
    this.clearCandidates();
    this.clearWorkStations();
  }

  /**
   * Fit map to show all markers
   */
  fitBounds(padding = 50) {
    const allMarkers = [
      this.markers.workA,
      this.markers.workB,
      ...this.markers.candidates
    ].filter(m => m !== null);

    if (allMarkers.length === 0) return;

    const group = L.featureGroup(allMarkers);
    this.map.fitBounds(group.getBounds().pad(0.1), {
      padding: [padding, padding],
      maxZoom: 14,
    });
  }

  /**
   * Toggle route visibility
   */
  toggleRoutes() {
    this.routesVisible = !this.routesVisible;
    
    this.routeLayers.forEach(layer => {
      if (this.routesVisible) {
        layer.setStyle({ opacity: 0.7 });
      } else {
        layer.setStyle({ opacity: 0.1 });
      }
    });

    return this.routesVisible;
  }

  /**
   * Zoom to a specific station
   */
  zoomToStation(latitude, longitude, zoom = 14) {
    this.map.setView([latitude, longitude], zoom, {
      animate: true,
      duration: 0.5,
    });
  }

  /**
   * Highlight a specific candidate
   */
  highlightCandidate(candidateId) {
    this.markers.candidates.forEach(marker => {
      const options = marker.options;
      if (options.candidateId === candidateId) {
        marker.openPopup();
      }
    });
  }

  /**
   * Get map bounds
   */
  getBounds() {
    return this.map.getBounds();
  }

  /**
   * Set map view
   */
  setView(lat, lng, zoom) {
    this.map.setView([lat, lng], zoom);
  }
}