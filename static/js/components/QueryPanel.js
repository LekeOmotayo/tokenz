/**
 * Query Panel Component
 * Manages prompt input, preset buttons, threshold slider, and evaluate triggers.
 */

import { SAMPLE_PRESETS } from '../api.js';

export class QueryPanelComponent {
  constructor({ onEvaluate }) {
    this.promptInput = document.getElementById('promptInput');
    this.thresholdSlider = document.getElementById('thresholdSlider');
    this.thresholdDisplay = document.getElementById('thresholdDisplay');
    this.evaluateBtn = document.getElementById('evaluateBtn');
    this.presetContainer = document.getElementById('presetContainer');
    this.onEvaluate = onEvaluate;

    this._bindEvents();
    this._renderPresets();
  }

  _bindEvents() {
    if (this.thresholdSlider) {
      this.thresholdSlider.addEventListener('input', (e) => {
        if (this.thresholdDisplay) {
          this.thresholdDisplay.innerText = parseFloat(e.target.value).toFixed(2);
        }
      });
    }

    if (this.evaluateBtn) {
      this.evaluateBtn.addEventListener('click', () => {
        if (this.onEvaluate) {
          this.onEvaluate(this.getPrompt(), this.getThreshold());
        }
      });
    }
  }

  _renderPresets() {
    if (!this.presetContainer) return;
    this.presetContainer.innerHTML = '';

    SAMPLE_PRESETS.forEach(p => {
      const btn = document.createElement('button');
      btn.className = 'preset-btn';
      btn.innerText = p.label;
      btn.addEventListener('click', () => {
        this.setPrompt(p.query);
        if (this.onEvaluate) {
          this.onEvaluate(p.query, this.getThreshold());
        }
      });
      this.presetContainer.appendChild(btn);
    });
  }

  getPrompt() {
    return this.promptInput ? this.promptInput.value.trim() : '';
  }

  setPrompt(text) {
    if (this.promptInput) {
      this.promptInput.value = text;
    }
  }

  getThreshold() {
    return this.thresholdSlider ? parseFloat(this.thresholdSlider.value) : 0.80;
  }

  setLoading(loading) {
    if (this.evaluateBtn) {
      this.evaluateBtn.disabled = loading;
      this.evaluateBtn.innerHTML = loading
        ? '<span>⏳</span> Searching SQLite Vectors...'
        : '<span>🔍</span> Evaluate Semantic Query';
    }
  }
}
