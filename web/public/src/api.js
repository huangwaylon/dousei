/**
 * API Client for Train Commute Optimizer
 * Handles all communication with the FastAPI backend
 */

export class ApiClient {
  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic fetch wrapper with error handling
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  /**
   * Search for stations by query
   */
  async searchStations(query, limit = 10) {
    const params = new URLSearchParams({ q: query, limit: limit.toString() });
    return await this.request(`/stations/search?${params}`);
  }

  /**
   * Get station details by ID
   */
  async getStation(stationId) {
    return await this.request(`/stations/${encodeURIComponent(stationId)}`);
  }

  /**
   * Analyze commute options
   */
  async analyzeCommute(stationA, stationB, options = {}) {
    const body = {
      station_a: stationA,
      station_b: stationB,
      top_n: options.topN || 10,
      max_time: options.maxTime || 120,
    };

    return await this.request('/analyze', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Get all railway lines
   */
  async getRailways() {
    return await this.request('/railways');
  }

  /**
   * Health check
   */
  async healthCheck() {
    return await this.request('/health');
  }
}

// Export singleton instance
export const api = new ApiClient();