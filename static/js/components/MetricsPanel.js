/**
 * Metrics Panel Component
 * Displays live Cache Status (HIT/MISS), similarity score, latency, and response box.
 */

export class MetricsPanelComponent {
  constructor() {
    this.cacheStatus = document.getElementById('cacheStatus');
    this.simScore = document.getElementById('simScore');
    this.retrievalLatency = document.getElementById('retrievalLatency');
    this.costSavings = document.getElementById('costSavings');
    this.latencyBarFill = document.getElementById('latencyBarFill');
    this.latencySavedText = document.getElementById('latencySavedText');
    this.responseBox = document.getElementById('responseBox');
  }

  render(evalResult) {
    if (!evalResult) return;

    if (evalResult.hit && evalResult.result) {
      const r = evalResult.result;
      this.cacheStatus.innerText = r.is_exact_match ? 'CACHE HIT (EXACT B-TREE)' : 'CACHE HIT (SEMANTIC VECTOR)';
      this.cacheStatus.style.color = '#34d399';

      this.simScore.innerText = `${r.similarity_score.toFixed(4)} (${(r.similarity_score * 100).toFixed(1)}%)`;
      this.retrievalLatency.innerText = `${r.retrieval_latency_ms.toFixed(3)} ms`;
      this.costSavings.innerText = `$${r.dollars_saved.toFixed(6)} (${r.total_tokens_saved} tokens)`;

      // Latency speedup bar
      if (this.latencyBarFill) {
        this.latencyBarFill.style.width = '100%';
      }
      if (this.latencySavedText) {
        this.latencySavedText.innerText = `${r.latency_saved_ms.toFixed(0)} ms saved vs cloud API`;
      }

      this.responseBox.innerText = r.response;
      this.responseBox.style.color = '#38bdf8';
    } else {
      this.cacheStatus.innerText = 'CACHE MISS (LLM INVOCATION REQUIRED)';
      this.cacheStatus.style.color = '#f87171';

      this.simScore.innerText = 'Below Threshold';
      this.retrievalLatency.innerText = '0.000 ms';
      this.costSavings.innerText = '$0.000000 (Fresh tokens)';

      if (this.latencyBarFill) {
        this.latencyBarFill.style.width = '0%';
      }
      if (this.latencySavedText) {
        this.latencySavedText.innerText = '0 ms saved (Cache Miss)';
      }

      this.responseBox.innerText = `[FORWARDING TO UPSTREAM LLM PROVIDER]\n\nQuery was not found in the local semantic cache with similarity score >= threshold. Upstream API call would be dispatched, and the resulting response will be persisted into SQLite.`;
      this.responseBox.style.color = '#94a3b8';
    }
  }
}
