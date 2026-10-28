/**
 * Entries Table Component
 * Displays persistent SQLite cache entries with hit counters and token economics.
 */

export class EntriesTableComponent {
  constructor({ onRefresh, onClear, onSeed }) {
    this.tbody = document.getElementById('entriesTableBody');
    this.refreshBtn = document.getElementById('refreshEntriesBtn');
    this.clearBtn = document.getElementById('clearCacheBtn');
    this.seedBtn = document.getElementById('seedCacheBtn');

    this.onRefresh = onRefresh;
    this.onClear = onClear;
    this.onSeed = onSeed;

    this._bindEvents();
  }

  _bindEvents() {
    if (this.refreshBtn) {
      this.refreshBtn.addEventListener('click', () => {
        if (this.onRefresh) this.onRefresh();
      });
    }
    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', () => {
        if (confirm("Are you sure you want to clear all cached entries in SQLite?")) {
          if (this.onClear) this.onClear();
        }
      });
    }
    if (this.seedBtn) {
      this.seedBtn.addEventListener('click', () => {
        if (this.onSeed) this.onSeed();
      });
    }
  }

  render(entries = []) {
    if (!this.tbody) return;
    this.tbody.innerHTML = '';

    if (entries.length === 0) {
      this.tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #64748b; padding: 2rem;">No cached entries in SQLite. Click 'Seed Knowledge Base' to load sample prompts.</td></tr>`;
      return;
    }

    entries.forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong style="color: #cbd5e1;">${this._escapeHtml(item.prompt)}</strong></td>
        <td><span style="font-size: 0.8rem; color: #94a3b8; font-family: monospace;">${this._escapeHtml(item.response.substring(0, 60))}...</span></td>
        <td><span style="font-size: 0.75rem; background: rgba(14, 165, 233, 0.15); color: #38bdf8; padding: 2px 6px; border-radius: 4px;">${item.model}</span></td>
        <td><strong style="color: #34d399;">${item.hit_count}</strong></td>
        <td><span style="color: #f59e0b; font-family: monospace;">${item.prompt_tokens + item.completion_tokens}</span></td>
      `;
      this.tbody.appendChild(tr);
    });
  }

  _escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
