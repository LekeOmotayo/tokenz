/**
 * Main Application Orchestrator for Leke Local Token Cache
 * Connects QueryPanel, MetricsPanel, StatsBar, and EntriesTable.
 */

import { ApiService } from './api.js';
import { QueryPanelComponent } from './components/QueryPanel.js';
import { MetricsPanelComponent } from './components/MetricsPanel.js';
import { StatsBarComponent } from './components/StatsBar.js';
import { EntriesTableComponent } from './components/EntriesTable.js';

class App {
  constructor() {
    this.api = new ApiService();
    this.metrics = new MetricsPanelComponent();
    this.stats = new StatsBarComponent();

    this.queryPanel = new QueryPanelComponent({
      onEvaluate: (prompt, threshold) => this.handleQuery(prompt, threshold)
    });

    this.entriesTable = new EntriesTableComponent({
      onRefresh: () => this.refreshEntries(),
      onClear: () => this.handleClear(),
      onSeed: () => this.handleSeed()
    });

    this.serverBadge = document.getElementById('serverBadge');
    this.serverBadgeText = document.getElementById('serverBadgeText');
  }

  async init() {
    const health = await this.api.checkHealth();
    this._updateServerStatus(health);

    await this.refreshStats();
    await this.refreshEntries();

    // Trigger initial query evaluation
    const initialPrompt = this.queryPanel.getPrompt();
    if (initialPrompt) {
      await this.handleQuery(initialPrompt, this.queryPanel.getThreshold());
    }
  }

  async handleQuery(prompt, threshold) {
    if (!prompt) return;
    this.queryPanel.setLoading(true);

    try {
      const result = await this.api.queryCache(prompt, threshold);
      this.metrics.render(result);
      if (result.stats) {
        this.stats.render(result.stats);
      }
      await this.refreshEntries();
    } catch (e) {
      console.error('Query error:', e);
    } finally {
      this.queryPanel.setLoading(false);
    }
  }

  async refreshStats() {
    const statsData = await this.api.getStats();
    this.stats.render(statsData);
  }

  async refreshEntries() {
    const entries = await this.api.getEntries();
    this.entriesTable.render(entries);
  }

  async handleClear() {
    await this.api.clearCache();
    await this.refreshStats();
    await this.refreshEntries();
    this.metrics.render({ hit: false });
  }

  async handleSeed() {
    await this.api.seedCache();
    await this.refreshStats();
    await this.refreshEntries();
  }

  _updateServerStatus({ connected, label }) {
    if (!this.serverBadge || !this.serverBadgeText) return;
    this.serverBadgeText.innerText = label;

    if (connected) {
      this.serverBadge.style.background = 'rgba(16, 185, 129, 0.15)';
      this.serverBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      this.serverBadge.style.color = '#34d399';
    } else {
      this.serverBadge.style.background = 'rgba(14, 165, 233, 0.15)';
      this.serverBadge.style.borderColor = 'rgba(14, 165, 233, 0.4)';
      this.serverBadge.style.color = '#38bdf8';
    }
  }
}

// Boot application
window.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
