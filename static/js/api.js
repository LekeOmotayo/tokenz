/**
 * API Service for Leke Local Token Cache
 * Handles communication with embedded Python REST API with offline fallback.
 */

export const SAMPLE_PRESETS = [
  { label: "France (Exact)", query: "What is the capital of France?" },
  { label: "France (Variation)", query: "what is the capital of france" },
  { label: "Python Sort", query: "How do I sort a dictionary by value in Python?" },
  { label: "Python Sort (Variation)", query: "how to sort dict by value in python" },
  { label: "TCP vs UDP", query: "What is the difference between TCP and UDP?" },
  { label: "Pizza (Cache Miss)", query: "What is the recipe for authentic Neapolitan pizza?" }
];

export class ApiService {
  constructor() {
    this.isConnected = false;
  }

  async checkHealth() {
    try {
      const resp = await fetch('/api/stats');
      if (resp.ok) {
        this.isConnected = true;
        return { connected: true, label: "Connected: Native SQLite Cache Engine" };
      }
    } catch (e) {
      // offline
    }
    this.isConnected = false;
    return { connected: false, label: "Client Mode (Offline Simulation)" };
  }

  async queryCache(prompt, threshold = 0.80) {
    if (this.isConnected) {
      try {
        const resp = await fetch('/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt, threshold })
        });
        if (resp.ok) {
          return await resp.json();
        }
      } catch (e) {
        console.warn('Backend call failed, using client fallback:', e);
      }
    }

    // Offline simulation
    return this._simulateQuery(prompt, threshold);
  }

  async getStats() {
    if (this.isConnected) {
      try {
        const resp = await fetch('/api/stats');
        if (resp.ok) return await resp.json();
      } catch (e) {}
    }
    return {
      total_cached_items: 4,
      total_cache_hits: 12,
      total_queries: 15,
      hit_rate_pct: 80.0,
      total_tokens_saved: 240,
      est_dollars_saved: 0.0018,
      est_time_saved_sec: 14.4
    };
  }

  async getEntries() {
    if (this.isConnected) {
      try {
        const resp = await fetch('/api/entries');
        if (resp.ok) return await resp.json();
      } catch (e) {}
    }
    return [
      { id: 1, prompt: "What is the capital of France?", response: "The capital of France is Paris, located along the Seine River.", model: "gpt-4o", hit_count: 8, prompt_tokens: 7, completion_tokens: 14 },
      { id: 2, prompt: "How do I sort a dictionary by value in Python?", response: "You can use sorted(my_dict.items(), key=lambda item: item[1]).", model: "gpt-4o", hit_count: 4, prompt_tokens: 12, completion_tokens: 16 }
    ];
  }

  async clearCache() {
    if (this.isConnected) {
      await fetch('/api/clear', { method: 'POST' });
    }
  }

  async seedCache() {
    if (this.isConnected) {
      await fetch('/api/seed', { method: 'POST' });
    }
  }

  _simulateQuery(prompt, threshold) {
    const pLower = prompt.toLowerCase().trim();
    if (pLower.includes("france")) {
      return {
        hit: true,
        result: {
          response: "The capital of France is Paris, located along the Seine River.",
          similarity_score: 0.942,
          retrieval_latency_ms: 0.42,
          latency_saved_ms: 1399.58,
          total_tokens_saved: 21,
          dollars_saved: 0.000157,
          is_exact_match: pLower === "what is the capital of france?"
        }
      };
    }
    if (pLower.includes("sort") && pLower.includes("dict")) {
      return {
        hit: true,
        result: {
          response: "You can use sorted(my_dict.items(), key=lambda item: item[1]).",
          similarity_score: 0.885,
          retrieval_latency_ms: 0.38,
          latency_saved_ms: 1399.62,
          total_tokens_saved: 28,
          dollars_saved: 0.00021,
          is_exact_match: false
        }
      };
    }
    return {
      hit: false,
      message: "Cache Miss: No cached response exceeds similarity threshold."
    };
  }
}
