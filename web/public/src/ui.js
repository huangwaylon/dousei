/**
 * UI Controller
 * Handles all UI interactions and state management
 */

export class UIController {
  constructor() {
    this.state = {
      stationA: null,
      stationB: null,
      candidates: [],
      selectedCandidateIndex: null,
      analysisOptions: {
        topN: 10,
        maxTime: 120,
      },
      isAnalyzing: false,
    };
  }

  /**
   * Initialize UI components
   */
  init() {
    this.setupSliders();
    console.log('UI initialized');
  }

  /**
   * Setup range sliders
   */
  setupSliders() {
    const topNSlider = document.getElementById('top-n');
    const topNValue = document.getElementById('top-n-value');
    const maxTimeSlider = document.getElementById('max-time');
    const maxTimeValue = document.getElementById('max-time-value');

    topNSlider?.addEventListener('input', (e) => {
      const value = parseInt(e.target.value);
      topNValue.textContent = value;
      this.state.analysisOptions.topN = value;
    });

    maxTimeSlider?.addEventListener('input', (e) => {
      const value = parseInt(e.target.value);
      maxTimeValue.textContent = value;
      this.state.analysisOptions.maxTime = value;
    });
  }

  /**
   * Show loading state for analyze button
   */
  setAnalyzing(isAnalyzing) {
    this.state.isAnalyzing = isAnalyzing;
    
    const button = document.getElementById('analyze-btn');
    const btnText = button?.querySelector('.btn-text');
    const btnLoader = button?.querySelector('.btn-loader');

    if (isAnalyzing) {
      button?.classList.add('loading');
      if (btnText) btnText.style.display = 'none';
      if (btnLoader) btnLoader.style.display = 'inline-block';
    } else {
      button?.classList.remove('loading');
      if (btnText) btnText.style.display = 'inline';
      if (btnLoader) btnLoader.style.display = 'none';
    }
  }

  /**
   * Update analyze button state
   */
  updateAnalyzeButton() {
    const button = document.getElementById('analyze-btn');
    const canAnalyze = this.state.stationA && this.state.stationB && !this.state.isAnalyzing;
    
    if (button) {
      button.disabled = !canAnalyze;
    }
  }

  /**
   * Display suggestions dropdown
   */
  displaySuggestions(suggestions, targetId) {
    const container = document.getElementById(`suggestions-${targetId}`);
    if (!container) return;

    if (suggestions.length === 0) {
      container.innerHTML = '';
      return;
    }

    container.innerHTML = suggestions.map(station => `
      <div class="suggestion-item" data-station-id="${station.id}" data-target="${targetId}">
        <div class="suggestion-title">${station.title} (${station.title_en})</div>
        <div class="suggestion-meta">${station.railway_name} • ${station.operator}</div>
      </div>
    `).join('');
  }

  /**
   * Show selected station
   */
  showSelectedStation(station, targetId) {
    const container = document.getElementById(`selected-${targetId}`);
    const inputWrapper = container?.previousElementSibling;
    const input = inputWrapper?.querySelector('.search-input');
    const clearBtn = inputWrapper?.querySelector('.clear-btn');

    if (container && input) {
      container.innerHTML = `
        <div class="selected-station-name">${station.title} (${station.title_en})</div>
        <div class="selected-station-meta">${station.railway_name}</div>
      `;
      container.style.display = 'block';
      input.value = '';
      input.style.display = 'none';
      
      if (clearBtn) {
        clearBtn.style.display = 'block';
      }
    }

    // Update state
    if (targetId === 'a') {
      this.state.stationA = station;
    } else {
      this.state.stationB = station;
    }

    this.updateAnalyzeButton();
  }

  /**
   * Clear selected station
   */
  clearSelectedStation(targetId) {
    const container = document.getElementById(`selected-${targetId}`);
    const inputWrapper = container?.previousElementSibling;
    const input = inputWrapper?.querySelector('.search-input');
    const clearBtn = inputWrapper?.querySelector('.clear-btn');

    if (container && input) {
      container.style.display = 'none';
      container.innerHTML = '';
      input.style.display = 'block';
      input.value = '';
      
      if (clearBtn) {
        clearBtn.style.display = 'none';
      }
    }

    // Update state
    if (targetId === 'a') {
      this.state.stationA = null;
    } else {
      this.state.stationB = null;
    }

    this.updateAnalyzeButton();
  }

  /**
   * Show analysis info
   */
  showAnalysisInfo(text) {
    const container = document.getElementById('analysis-info');
    if (container) {
      container.textContent = text;
      container.style.display = 'block';
    }
  }

  /**
   * Hide analysis info
   */
  hideAnalysisInfo() {
    const container = document.getElementById('analysis-info');
    if (container) {
      container.style.display = 'none';
    }
  }

  /**
   * Display results
   */
  displayResults(candidates) {
    this.state.candidates = candidates;

    const emptyState = document.getElementById('results-empty');
    const resultsList = document.getElementById('results-list');
    const resultsActions = document.getElementById('results-actions');
    const mapLegend = document.getElementById('map-legend');

    if (emptyState) emptyState.style.display = 'none';
    if (resultsList) resultsList.style.display = 'block';
    if (resultsActions) resultsActions.style.display = 'flex';
    if (mapLegend) mapLegend.style.display = 'block';

    if (!resultsList) return;

    resultsList.innerHTML = candidates.map((candidate, index) => this.createCandidateCard(candidate, index)).join('');
  }

  /**
   * Create candidate card HTML
   */
  createCandidateCard(candidate, index) {
    const rank = index + 1;
    const balancePercent = (candidate.balance_score * 100).toFixed(0);
    const timeDiffColor = candidate.time_difference < 5 ? 'var(--color-success)' : 
                          candidate.time_difference < 10 ? 'var(--color-warning)' : 
                          'var(--color-danger)';

    return `
      <div class="candidate-card fade-in" data-candidate-index="${index}" data-station-id="${candidate.station_id}">
        <div class="rank-badge">#${rank}</div>
        <h3 class="card-title">${candidate.station_name}</h3>
        <div class="card-time">${candidate.total_time.toFixed(1)} min</div>
        
        <div class="balance-bar">
          <div class="balance-fill" style="width: ${balancePercent}%"></div>
        </div>
        
        <div class="card-stats">
          <div>
            <div class="stat-label">Time Difference</div>
            <div style="color: ${timeDiffColor}; font-weight: 600;">
              ${candidate.time_difference.toFixed(1)} min
            </div>
          </div>
          <div>
            <div class="stat-label">Balance Score</div>
            <div style="font-weight: 600;">${balancePercent}%</div>
          </div>
          <div>
            <div class="stat-label">Person A Time</div>
            <div>${candidate.route_from_a.total_time.toFixed(1)} min</div>
          </div>
          <div>
            <div class="stat-label">Person B Time</div>
            <div>${candidate.route_from_b.total_time.toFixed(1)} min</div>
          </div>
        </div>
        
        <div class="card-actions">
          <button class="btn-view" data-action="view-details" data-candidate-index="${index}">
            View Details
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Show route details modal
   */
  showRouteDetails(candidate) {
    const modal = document.getElementById('route-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');

    if (!modal || !modalBody) return;

    modalTitle.textContent = `Route Details - ${candidate.station_name}`;
    
    modalBody.innerHTML = `
      <div class="route-comparison">
        <div class="route-detail">
          <h3 class="route-header" style="color: var(--color-station-a);">
            Person A's Route
          </h3>
          <div style="margin-bottom: 1rem; color: var(--color-text-secondary);">
            <div>⏱️ ${candidate.route_from_a.total_time.toFixed(1)} minutes</div>
            <div>🚉 ${candidate.route_from_a.total_stops} stops</div>
            <div>🔄 ${candidate.route_from_a.transfers} transfers</div>
          </div>
          ${this.renderRouteSegments(candidate.route_from_a.segments)}
        </div>
        
        <div class="route-detail">
          <h3 class="route-header" style="color: var(--color-station-b);">
            Person B's Route
          </h3>
          <div style="margin-bottom: 1rem; color: var(--color-text-secondary);">
            <div>⏱️ ${candidate.route_from_b.total_time.toFixed(1)} minutes</div>
            <div>🚉 ${candidate.route_from_b.total_stops} stops</div>
            <div>🔄 ${candidate.route_from_b.transfers} transfers</div>
          </div>
          ${this.renderRouteSegments(candidate.route_from_b.segments)}
        </div>
      </div>
    `;

    modal.style.display = 'flex';
  }

  /**
   * Render route segments
   */
  renderRouteSegments(segments) {
    if (!segments || segments.length === 0) {
      return '<div style="color: var(--color-text-secondary);">Direct connection</div>';
    }

    return `
      <div class="route-segments">
        ${segments.map(segment => `
          <div class="segment ${segment.is_transfer ? 'transfer' : ''}">
            <div class="segment-railway">
              ${segment.is_transfer ? '🔄 Transfer' : `🚆 ${segment.railway_name}`}
            </div>
            <div class="segment-stations">
              ${segment.from_station_name} → ${segment.to_station_name}
            </div>
            <div class="segment-info">
              ${segment.is_transfer 
                ? `${segment.travel_time.toFixed(1)} min transfer time` 
                : `${segment.num_stops} stops, ${segment.travel_time.toFixed(1)} min`
              }
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  /**
   * Hide route details modal
   */
  hideRouteDetails() {
    const modal = document.getElementById('route-modal');
    if (modal) {
      modal.style.display = 'none';
    }
  }

  /**
   * Select a candidate
   */
  selectCandidate(index) {
    this.state.selectedCandidateIndex = index;

    // Update card styling
    document.querySelectorAll('.candidate-card').forEach((card, i) => {
      if (i === index) {
        card.classList.add('selected');
      } else {
        card.classList.remove('selected');
      }
    });
  }

  /**
   * Show error message
   */
  showError(message) {
    const resultsList = document.getElementById('results-list');
    const emptyState = document.getElementById('results-empty');

    if (resultsList) resultsList.style.display = 'none';
    if (emptyState) {
      emptyState.innerHTML = `
        <div class="empty-icon">⚠️</div>
        <h3>Error</h3>
        <p>${message}</p>
      `;
      emptyState.style.display = 'block';
    }
  }

  /**
   * Reset UI to initial state
   */
  reset() {
    // Clear station selections
    this.clearSelectedStation('a');
    this.clearSelectedStation('b');

    // Hide results
    const emptyState = document.getElementById('results-empty');
    const resultsList = document.getElementById('results-list');
    const resultsActions = document.getElementById('results-actions');
    const mapLegend = document.getElementById('map-legend');

    if (emptyState) {
      emptyState.innerHTML = `
        <div class="empty-icon">🔍</div>
        <h3>No Analysis Yet</h3>
        <p>Select two work stations and click "Analyze Routes" to find optimal living locations.</p>
      `;
      emptyState.style.display = 'block';
    }
    if (resultsList) resultsList.style.display = 'none';
    if (resultsActions) resultsActions.style.display = 'none';
    if (mapLegend) mapLegend.style.display = 'none';

    // Clear suggestions
    this.displaySuggestions([], 'a');
    this.displaySuggestions([], 'b');

    // Hide analysis info
    this.hideAnalysisInfo();

    // Reset state
    this.state = {
      stationA: null,
      stationB: null,
      candidates: [],
      selectedCandidateIndex: null,
      analysisOptions: {
        topN: parseInt(document.getElementById('top-n')?.value || '10'),
        maxTime: parseInt(document.getElementById('max-time')?.value || '120'),
      },
      isAnalyzing: false,
    };

    this.updateAnalyzeButton();
  }

  /**
   * Export results as JSON
   */
  exportJSON() {
    if (this.state.candidates.length === 0) return;

    const data = {
      work_stations: {
        a: this.state.stationA,
        b: this.state.stationB,
      },
      candidates: this.state.candidates,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `train-commute-results-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Export results as CSV
   */
  exportCSV() {
    if (this.state.candidates.length === 0) return;

    const headers = [
      'Rank',
      'Station Name',
      'Total Time (min)',
      'Time Difference (min)',
      'Balance Score',
      'Person A Time (min)',
      'Person A Stops',
      'Person A Transfers',
      'Person B Time (min)',
      'Person B Stops',
      'Person B Transfers',
    ];

    const rows = this.state.candidates.map((candidate, index) => [
      index + 1,
      candidate.station_name,
      candidate.total_time.toFixed(1),
      candidate.time_difference.toFixed(1),
      (candidate.balance_score * 100).toFixed(0) + '%',
      candidate.route_from_a.total_time.toFixed(1),
      candidate.route_from_a.total_stops,
      candidate.route_from_a.transfers,
      candidate.route_from_b.total_time.toFixed(1),
      candidate.route_from_b.total_stops,
      candidate.route_from_b.transfers,
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `train-commute-results-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }
}