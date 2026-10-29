document.addEventListener('DOMContentLoaded', () => {
  const promptInput = document.getElementById('prompt-input');
  const modelSelect = document.getElementById('model-select');
  const similaritySlider = document.getElementById('similarity-slider');
  const thresholdVal = document.getElementById('threshold-val');
  const queryBtn = document.getElementById('query-btn');
  const clearBtn = document.getElementById('clear-cache-btn');

  const roiDollars = document.getElementById('roi-dollars');
  const roiTokens = document.getElementById('roi-tokens');
  const roiLatency = document.getElementById('roi-latency');
  const roiRatio = document.getElementById('roi-ratio');

  const decisionBadge = document.getElementById('decision-badge');
  const telemetrySimilarity = document.getElementById('telemetry-similarity');
  const telemetryLatency = document.getElementById('telemetry-latency');
  const telemetryTokens = document.getElementById('telemetry-tokens');
  const telemetryCost = document.getElementById('telemetry-cost');
  const modelTag = document.getElementById('model-tag');
  const responseBody = document.getElementById('response-body');

  similaritySlider.addEventListener('input', () => {
    thresholdVal.textContent = parseFloat(similaritySlider.value).toFixed(2);
  });

  document.querySelectorAll('.sample-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      promptInput.value = pill.getAttribute('data-prompt');
      executeQuery();
    });
  });

  async function updateStats() {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      const s = data.stats || {};

      roiDollars.textContent = `$${(s.total_dollars_saved || 0).toFixed(6)}`;
      roiTokens.textContent = (s.total_tokens_saved || 0).toLocaleString();
      roiLatency.textContent = `${((s.total_latency_saved_ms || 0) / 1000).toFixed(2)}s`;
      roiRatio.textContent = `${(s.hit_ratio_percent || 0).toFixed(1)}%`;
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }

  async function executeQuery() {
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    queryBtn.disabled = true;
    queryBtn.textContent = 'Searching Vector Index...';

    const startTime = performance.now();

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          model: modelSelect.value,
          auto_seed: true
        })
      });

      const clientLatency = (performance.now() - startTime).toFixed(1);
      const data = await res.json();
      renderResult(data, clientLatency);
      updateStats();
    } catch (err) {
      console.error('Query failed:', err);
    } finally {
      queryBtn.disabled = false;
      queryBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        Execute Semantic Lookup
      `;
    }
  }

  function renderResult(data, clientLatency) {
    const isHit = data.status === 'HIT';

    decisionBadge.textContent = isHit ? (data.is_exact_match ? '⚡ EXACT HIT' : '🎯 SEMANTIC HIT') : '❌ CACHE MISS';
    decisionBadge.className = `decision-pill ${isHit ? 'status-hit' : 'status-miss'}`;

    telemetrySimilarity.textContent = (data.similarity_score || 0).toFixed(4);
    telemetryLatency.textContent = `${data.retrieval_latency_ms || clientLatency} ms`;
    telemetryTokens.textContent = data.tokens_saved || 0;
    telemetryCost.textContent = `$${(data.dollars_saved || 0).toFixed(6)}`;

    modelTag.textContent = data.model || modelSelect.value;
    responseBody.textContent = data.response || data.message || 'No response returned.';
  }

  queryBtn.addEventListener('click', executeQuery);

  clearBtn.addEventListener('click', async () => {
    if (confirm('Clear local SQLite vector cache?')) {
      await fetch('/api/clear', { method: 'POST' });
      decisionBadge.textContent = 'CLEARED';
      decisionBadge.className = 'decision-pill status-ready';
      telemetrySimilarity.textContent = '0.0000';
      telemetryLatency.textContent = '-- ms';
      telemetryTokens.textContent = '0';
      telemetryCost.textContent = '$0.000000';
      responseBody.textContent = 'Cache cleared. Submit new queries to re-seed.';
      updateStats();
    }
  });

  // Seed default query and fetch initial stats
  promptInput.value = "What is the capital of France?";
  updateStats();
});
