/* Nerdminer-HA Lovelace card. */

const DEFAULTS = {
  current: "current_hashrate",
  average_1m: "1_minute_average_hashrate",
  average_5m: "5_minute_average_hashrate",
  hardware: "hardware_hashrate",
  software: "software_hashrate",
  shares_accepted: "shares_accepted",
  shares_rejected: "shares_rejected",
  temperature: "board_temperature",
  uptime: "uptime",
};

const COLORS = {
  current: "#ffb454",
  average_1m: "#72d6c9",
  average_5m: "#8ca8ff",
  hardware: "#ffb454",
  software: "#e883ff",
  accepted: "#72d6c9",
  rejected: "#ff7189",
  temperature: "#ff8f70",
};

class NerdminerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    if (!config || !config.entity_prefix && !config.entities) {
      throw new Error("Set entity_prefix or entities in the Nerdminer card configuration");
    }
    this.config = {
      title: "Nerdminer-HA",
      hours_to_show: 6,
      ...config,
    };
    this._history = {};
    this._loading = false;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.config) return;
    this._render();
    if (!this._historyLoadedFor(hass)) this._loadHistory();
  }

  getCardSize() {
    return 7;
  }

  _entity(key) {
    if (this.config.entities?.[key]) return this.config.entities[key];
    const suffix = DEFAULTS[key];
    return suffix && this.config.entity_prefix ? `sensor.${this.config.entity_prefix}_${suffix}` : null;
  }

  _state(key) {
    const entity = this._entity(key);
    return entity ? this._hass?.states[entity] : null;
  }

  _value(key) {
    const state = this._state(key);
    const value = Number(state?.state);
    return Number.isFinite(value) ? value : null;
  }

  _display(value, digits = 1) {
    if (value === null || value === undefined) return "--";
    return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits });
  }

  _historyLoadedFor(hass) {
    return this._historyEntityCount === Object.keys(hass?.states || {}).length && this._historyAt;
  }

  async _loadHistory() {
    if (this._loading || !this._hass) return;
    const entities = Object.values(DEFAULTS).map((suffix) => this._entity(Object.keys(DEFAULTS).find((key) => DEFAULTS[key] === suffix))).filter(Boolean);
    if (!entities.length || !this._hass.callApi) return;
    this._loading = true;
    const start = new Date(Date.now() - Number(this.config.hours_to_show) * 3600000).toISOString();
    try {
      const path = `history/period/${encodeURIComponent(start)}?filter_entity_id=${encodeURIComponent(entities.join(","))}&minimal_response&no_attributes`;
      const response = await this._hass.callApi("GET", path);
      this._history = Object.fromEntries((response || []).map((series) => [series[0]?.entity_id, series]));
      this._historyEntityCount = Object.keys(this._hass.states).length;
      this._historyAt = Date.now();
      this._render();
    } catch (error) {
      this._history = {};
      this._render();
      console.warn("Nerdminer card could not load history", error);
    } finally {
      this._loading = false;
    }
  }

  _series(key) {
    return (this._history[this._entity(key)] || []).map((point) => ({
      time: new Date(point.last_changed || point.last_updated).getTime(),
      value: Number(point.state),
    })).filter((point) => Number.isFinite(point.value));
  }

  _path(series, width, height, min, max) {
    if (!series.length) return "";
    return this._coordinates(series, width, height, min, max).map((point, index) =>
      `${index ? "L" : "M"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`
    ).join(" ");
  }

  _coordinates(series, width, height, min, max) {
    const range = max - min || 1;
    return series.map((point, index) => {
      const x = series.length === 1 ? width / 2 : (index / (series.length - 1)) * width;
      const y = height - ((point.value - min) / range) * height;
      return { x, y: Math.max(0, Math.min(height, y)) };
    });
  }

  _areaPath(upper, lower, width, height, max) {
    const top = this._coordinates(upper, width, height, 0, max);
    const bottom = this._coordinates(lower, width, height, 0, max).reverse();
    return [...top, ...bottom].map((point, index) =>
      `${index ? "L" : "M"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`
    ).join(" ") + " Z";
  }

  _lineChart(seriesList, colors, stacked = false) {
    const width = 620;
    const height = 166;
    const all = seriesList.flat();
    if (!all.length) return `<div class="empty">History will appear after the first refresh.</div>`;
    const max = stacked ? Math.max(...seriesList[0].map((_, index) => seriesList.reduce((sum, series) => sum + (series[index]?.value || 0), 0)), 1) : Math.max(...all.map((point) => point.value), 1);
    const min = stacked ? 0 : Math.min(...all.map((point) => point.value), 0);
    const paths = seriesList.map((series, index) => {
      if (!stacked) return `<path d="${this._path(series, width, height, min, max)}" stroke="${colors[index]}"/>`;
      const upper = series.map((point, pointIndex) => ({ ...point, value: seriesList.slice(0, index + 1).reduce((sum, item) => sum + (item[pointIndex]?.value || 0), 0) }));
      const lower = series.map((point, pointIndex) => ({ ...point, value: seriesList.slice(0, index).reduce((sum, item) => sum + (item[pointIndex]?.value || 0), 0) }));
      return `<path d="${this._areaPath(upper, lower, width, height, max)}" stroke="${colors[index]}" fill="${colors[index]}" fill-opacity=".34"/>`;
    }).join("");
    return `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img"><line x1="0" y1="${height}" x2="${width}" y2="${height}" class="axis"/><line x1="0" y1="${height / 2}" x2="${width}" y2="${height / 2}" class="grid"/>${paths}</svg>`;
  }

  _render() {
    if (!this.config || !this._hass) return;
    const current = this._value("current");
    const avg1 = this._value("average_1m");
    const avg5 = this._value("average_5m");
    const temperature = this._value("temperature");
    const uptime = this._value("uptime");
    const accepted = this._value("shares_accepted");
    const rejected = this._value("shares_rejected");
    const title = this.config.title;
    const avgChart = this._lineChart([this._series("average_1m"), this._series("average_5m")], [COLORS.average_1m, COLORS.average_5m]);
    const splitChart = this._lineChart([this._series("hardware"), this._series("software")], [COLORS.hardware, COLORS.software], true);
    this.shadowRoot.innerHTML = `<ha-card><style>
      :host { --nm-ink:#edf3f4; --nm-muted:#91a5a7; --nm-panel:#152327; --nm-line:#294044; display:block; }
      ha-card { overflow:hidden; color:var(--nm-ink); background:linear-gradient(145deg,#101b20,#182d2e 58%,#213d39); border:1px solid #315154; border-radius:18px; box-shadow:0 10px 28px rgba(0,0,0,.22); }
      .top { padding:20px 22px 16px; display:flex; justify-content:space-between; align-items:flex-start; background:radial-gradient(circle at 90% 0%,rgba(114,214,201,.18),transparent 42%); }
      h2 { margin:0; font:700 19px/1.1 ui-rounded,"Avenir Next",sans-serif; letter-spacing:.02em; } .eyebrow { color:#72d6c9; font:700 10px/1.2 monospace; letter-spacing:.18em; text-transform:uppercase; margin-bottom:7px; }
      .live { display:flex; align-items:center; gap:7px; color:#b6cbca; font-size:11px; } .dot { width:7px; height:7px; border-radius:50%; background:#72d6c9; box-shadow:0 0 12px #72d6c9; }
      .hero { padding:0 22px 18px; } .hero-value { font:700 42px/1 ui-rounded,"Avenir Next",sans-serif; letter-spacing:-.03em; } .hero-unit { color:#91a5a7; font-size:13px; margin-left:7px; }
      .metrics { display:grid; grid-template-columns:repeat(3,1fr); gap:9px; padding:0 22px 20px; } .metric { background:rgba(8,20,23,.35); border:1px solid rgba(100,143,143,.25); border-radius:11px; padding:11px 12px; } .label { color:#91a5a7; font-size:10px; text-transform:uppercase; letter-spacing:.08em; } .metric strong { display:block; margin-top:5px; font-size:16px; } .metric strong em { color:#91a5a7; font-style:normal; font-size:10px; font-weight:400; }
      .section { padding:16px 22px 18px; border-top:1px solid rgba(100,143,143,.2); } .section-head { display:flex; justify-content:space-between; margin-bottom:12px; } .section-title { font-size:12px; font-weight:700; } .legend { display:flex; gap:12px; color:#91a5a7; font-size:10px; } .legend i { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:4px; background:var(--c); }
      .chart { height:166px; margin:0 -4px; } svg { width:100%; height:100%; overflow:visible; } path { fill:none; stroke-width:3; stroke-linecap:round; stroke-linejoin:round; filter:drop-shadow(0 2px 4px rgba(0,0,0,.35)); } .axis,.grid { stroke:var(--nm-line); stroke-width:1; } .grid { opacity:.55; stroke-dasharray:3 5; } .empty { height:166px; display:grid; place-items:center; color:#91a5a7; font-size:12px; border:1px dashed #315154; border-radius:10px; }
      .footer { display:grid; grid-template-columns:repeat(3,1fr); gap:9px; padding:16px 22px 20px; border-top:1px solid rgba(100,143,143,.2); } .foot-value { display:block; margin-top:4px; font-size:15px; } @media(max-width:500px) { .metrics { grid-template-columns:repeat(2,1fr); } .hero-value { font-size:35px; } .top,.hero,.metrics,.section,.footer { padding-left:16px; padding-right:16px; } }
    </style><div class="top"><div><div class="eyebrow">AXEHUB TELEMETRY</div><h2>${title}</h2></div><div class="live"><span class="dot"></span>LIVE</div></div><div class="hero"><span class="hero-value">${this._display(current, 0)}</span><span class="hero-unit">kH/s CURRENT</span></div><div class="metrics"><div class="metric"><span class="label">1 min average</span><strong>${this._display(avg1)} <em>kH/s</em></strong></div><div class="metric"><span class="label">5 min average</span><strong>${this._display(avg5)} <em>kH/s</em></strong></div><div class="metric"><span class="label">hardware</span><strong>${this._display(this._value("hardware"), 0)} <em>kH/s</em></strong></div><div class="metric"><span class="label">software</span><strong>${this._display(this._value("software"), 0)} <em>kH/s</em></strong></div><div class="metric"><span class="label">accepted</span><strong>${this._display(accepted, 0)}</strong></div><div class="metric"><span class="label">rejected</span><strong>${this._display(rejected, 0)}</strong></div></div><div class="section"><div class="section-head"><span class="section-title">Rolling hashrate</span><span class="legend"><span><i style="--c:${COLORS.average_1m}"></i>1 min</span><span><i style="--c:${COLORS.average_5m}"></i>5 min</span></span></div><div class="chart">${avgChart}</div></div><div class="section"><div class="section-head"><span class="section-title">Hashrate composition</span><span class="legend"><span><i style="--c:${COLORS.hardware}"></i>HW</span><span><i style="--c:${COLORS.software}"></i>SW</span></span></div><div class="chart">${splitChart}</div></div><div class="footer"><div><span class="label">board temperature</span><strong class="foot-value">${this._display(temperature, 1)} °C</strong></div><div><span class="label">uptime</span><strong class="foot-value">${this._display(uptime, 1)} h</strong></div><div><span class="label">refresh</span><strong class="foot-value">30 sec</strong></div></div></ha-card>`;
  }
}

customElements.define("nerdminer-card", NerdminerCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "nerdminer-card", name: "Nerdminer-HA", description: "Nerdminer telemetry graphs and metrics" });
