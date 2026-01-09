/**
 * Main Application Entry Point
 * Train Commute Optimizer - 2026
 */

import { api } from './api.js';
import { MapController } from './map.js';
import { UIController } from './ui.js';

// Initialize controllers
const map = new MapController('map');
const ui = new UIController();

// Debounce helper
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Station search handler
const handleStationSearch = debounce(async (query, targetId) => {
  if (query.length < 2) {
    ui.displaySuggestions([], targetId);
    return;
  }

  try {
    const response = await api.searchStations(query, 10);
    ui.displaySuggestions(response.stations, targetId);
  } catch (error) {
    console.error('Search error:', error);
    ui.displaySuggestions([], targetId);
  }
}, 300);

// Handle station selection
function handleStationSelection(station, targetId) {
  ui.showSelectedStation(station, targetId);
  ui.displaySuggestions([], targetId);
  
  // Add marker to map
  map.addWorkStation(
    {
      latitude: station.latitude,
      longitude: station.longitude,
      name: station.title,
    },
    targetId
  );
  
  // Fit map if both stations are selected
  if (ui.state.stationA && ui.state.stationB) {
    map.fitBounds();
  }
}

// Handle analysis
async function handleAnalyze() {
  if (!ui.state.stationA || !ui.state.stationB) {
    return;
  }

  ui.setAnalyzing(true);
  ui.hideAnalysisInfo();
  map.clearRoutes();
  map.clearCandidates();

  try {
    const response = await api.analyzeCommute(
      ui.state.stationA.id,
      ui.state.stationB.id,
      {
        topN: ui.state.analysisOptions.topN,
        maxTime: ui.state.analysisOptions.maxTime,
      }
    );

    console.log('Analysis complete:', response);

    // Display results
    ui.displayResults(response.candidates);
    
    // Add candidate markers to map
    response.candidates.forEach((candidate, index) => {
      map.addCandidateMarker(candidate, index + 1);
    });

    // Draw routes for top 3 candidates
    response.candidates.slice(0, 3).forEach((candidate, index) => {
      map.drawCandidateRoutes(candidate, index === 0);
    });

    // Fit map to show all markers
    setTimeout(() => {
      map.fitBounds();
    }, 100);

    // Show analysis info
    ui.showAnalysisInfo(
      `Found ${response.candidates.length} candidates in ${response.computation_time.toFixed(2)}s`
    );

  } catch (error) {
    console.error('Analysis error:', error);
    ui.showError(error.message || 'Analysis failed. Please try again.');
  } finally {
    ui.setAnalyzing(false);
  }
}

// Handle candidate card click
function handleCandidateClick(index) {
  const candidate = ui.state.candidates[index];
  if (!candidate) return;

  ui.selectCandidate(index);
  
  // Clear existing routes
  map.clearRoutes();
  
  // Draw routes for selected candidate
  map.drawCandidateRoutes(candidate, true);
  
  // Draw faded routes for other top candidates
  ui.state.candidates.slice(0, 5).forEach((c, i) => {
    if (i !== index) {
      map.drawCandidateRoutes(c, false);
    }
  });
  
  // Zoom to candidate
  map.zoomToStation(candidate.latitude, candidate.longitude, 13);
}

// Handle view details
function handleViewDetails(index) {
  const candidate = ui.state.candidates[index];
  if (!candidate) return;
  
  ui.showRouteDetails(candidate);
}

// Handle reset
function handleReset() {
  ui.reset();
  map.clearAll();
  map.setView(35.6762, 139.6503, 11);
}

// Setup event listeners
function setupEventListeners() {
  // Station A search
  const stationAInput = document.getElementById('station-a-input');
  stationAInput?.addEventListener('input', (e) => {
    handleStationSearch(e.target.value, 'a');
  });

  // Station B search
  const stationBInput = document.getElementById('station-b-input');
  stationBInput?.addEventListener('input', (e) => {
    handleStationSearch(e.target.value, 'b');
  });

  // Clear buttons
  document.getElementById('clear-a')?.addEventListener('click', () => {
    ui.clearSelectedStation('a');
    map.clearWorkStations();
    if (ui.state.stationA) {
      map.addWorkStation(
        {
          latitude: ui.state.stationA.latitude,
          longitude: ui.state.stationA.longitude,
          name: ui.state.stationA.title,
        },
        'a'
      );
    }
  });

  document.getElementById('clear-b')?.addEventListener('click', () => {
    ui.clearSelectedStation('b');
    map.clearWorkStations();
    if (ui.state.stationB) {
      map.addWorkStation(
        {
          latitude: ui.state.stationB.latitude,
          longitude: ui.state.stationB.longitude,
          name: ui.state.stationB.title,
        },
        'b'
      );
    }
  });

  // Suggestion clicks (event delegation)
  document.addEventListener('click', async (e) => {
    const suggestionItem = e.target.closest('.suggestion-item');
    if (suggestionItem) {
      const stationId = suggestionItem.dataset.stationId;
      const targetId = suggestionItem.dataset.target;
      
      try {
        const station = await api.getStation(stationId);
        handleStationSelection(station, targetId);
      } catch (error) {
        console.error('Error fetching station:', error);
      }
    }
  });

  // Analyze button
  document.getElementById('analyze-btn')?.addEventListener('click', handleAnalyze);

  // Reset button
  document.getElementById('reset-btn')?.addEventListener('click', handleReset);

  // Map controls
  document.getElementById('fit-bounds-btn')?.addEventListener('click', () => {
    map.fitBounds();
  });

  document.getElementById('toggle-routes-btn')?.addEventListener('click', () => {
    const visible = map.toggleRoutes();
    const btn = document.getElementById('toggle-routes-btn');
    if (btn) {
      btn.textContent = visible ? '👁️ Toggle Routes' : '👁️‍🗨️ Toggle Routes';
    }
  });

  // Results clicks (event delegation)
  document.addEventListener('click', (e) => {
    // Candidate card click
    const candidateCard = e.target.closest('.candidate-card');
    if (candidateCard && !e.target.closest('[data-action]')) {
      const index = parseInt(candidateCard.dataset.candidateIndex);
      handleCandidateClick(index);
      return;
    }

    // View details button
    const viewDetailsBtn = e.target.closest('[data-action="view-details"]');
    if (viewDetailsBtn) {
      const index = parseInt(viewDetailsBtn.dataset.candidateIndex);
      handleViewDetails(index);
      return;
    }
  });

  // Modal close
  document.getElementById('modal-close')?.addEventListener('click', () => {
    ui.hideRouteDetails();
  });

  // Close modal on background click
  document.getElementById('route-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'route-modal') {
      ui.hideRouteDetails();
    }
  });

  // Export buttons
  document.getElementById('export-json-btn')?.addEventListener('click', () => {
    ui.exportJSON();
  });

  document.getElementById('export-csv-btn')?.addEventListener('click', () => {
    ui.exportCSV();
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // ESC to close modal
    if (e.key === 'Escape') {
      ui.hideRouteDetails();
    }
    
    // Enter to analyze (if both stations selected)
    if (e.key === 'Enter' && ui.state.stationA && ui.state.stationB && !ui.state.isAnalyzing) {
      const activeElement = document.activeElement;
      if (activeElement?.tagName !== 'INPUT') {
        handleAnalyze();
      }
    }
  });
}

// Initialize app
async function init() {
  console.log('🚂 Train Commute Optimizer initializing...');
  
  // Initialize UI
  ui.init();
  
  // Initialize map
  map.init();
  
  // Setup event listeners
  setupEventListeners();
  
  // Check API health
  try {
    const health = await api.healthCheck();
    console.log('✅ API health:', health);
  } catch (error) {
    console.error('⚠️ API health check failed:', error);
  }
  
  console.log('✅ Application ready!');
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Export for debugging
window.app = { map, ui, api };