/**
 * Stats Bar Component
 * Displays cumulative telemetry metrics in top cards.
 */

export class StatsBarComponent {
  constructor() {
    this.metricCachedItems = document.getElementById('metricCachedItems');
    this.metricCacheHits = document.getElementById('metricCacheHits');
    this.metricTokensSaved = document.getElementById('metricTokensSaved');
    this.metricDollarsSaved = document.getElementById('metricDollarsSaved');
  }

  render(stats) {
    if (!stats) return;

    if (this.metricCachedItems) {
      this.metricCachedItems.innerHTML = `${stats.total_cached_items || 0} <span class="metric-sub">SQLite entries</span>`;
    }
    if (this.metricCacheHits) {
      this.metricCacheHits.innerHTML = `${stats.total_cache_hits || 0} <span class="metric-sub">Hit Rate: ${stats.hit_rate_pct || 0}%</span>`;
    }
    if (this.metricTokensSaved) {
      this.metricTokensSaved.innerHTML = `${stats.total_tokens_saved || 0} <span class="metric-sub">tokens bypassed</span>`;
    }
    if (this.metricDollarsSaved) {
      this.metricDollarsSaved.innerHTML = `$${(stats.est_dollars_saved || 0).toFixed(4)} <span class="metric-sub">ROI savings</span>`;
    }
  }
}
