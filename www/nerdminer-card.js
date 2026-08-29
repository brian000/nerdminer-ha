/* Nerdminer-HA Lovelace cards using Home Assistant's native card rendering. */

const MINER_SUFFIXES = {
  current: "current_hashrate",
  average_1m: "1_minute_average_hashrate",
  average_5m: "5_minute_average_hashrate",
  hardware: "hardware_hashrate",
  software: "software_hashrate",
  shares_accepted: "shares_accepted",
  shares_rejected: "shares_rejected",
  best_diff: "best_difficulty",
  best_session_diff: "best_session_difficulty",
  valid_blocks: "valid_blocks",
  temperature: "board_temperature",
  uptime: "uptime",
  cpu_frequency: "cpu_frequency",
  mac: "mac_address",
};

const formatValue = (value, digits = 1) => {
  if (value === undefined || value === null || value === "unknown" || value === "unavailable") return "-";
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString(undefined, { maximumFractionDigits: digits }) : value;
};

const editorSchema = (farm = false) => [
  { name: "title", selector: { text: {} } },
  ...(farm ? [] : [{ name: "entity_prefix", selector: { text: {} } }]),
  { name: "hours_to_show", selector: { number: { min: 1, max: 168, step: 1, mode: "box" } } },
];

class NerdminerCardEditor extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;
    const form = document.createElement("ha-form");
    form.hass = this._hass;
    form.data = this._config;
    form.schema = editorSchema(false);
    form.computeLabel = (schema) => ({ title: "Title", entity_prefix: "Entity prefix", hours_to_show: "Hours of history" }[schema.name]);
    form.addEventListener("value-changed", (event) => this._changed(event.detail.value));
    this.innerHTML = "";
    this.append(form);
  }

  _changed(value) {
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: { ...this._config, ...value } }, bubbles: true, composed: true,
    }));
  }
}

class NerdminerFarmCardEditor extends NerdminerCardEditor {
  _render() {
    if (!this._hass || !this._config) return;
    const form = document.createElement("ha-form");
    form.hass = this._hass;
    form.data = this._config;
    form.schema = editorSchema(true);
    form.computeLabel = (schema) => ({ title: "Title", hours_to_show: "Hours of history" }[schema.name]);
    form.addEventListener("value-changed", (event) => this._changed(event.detail.value));
    this.innerHTML = "";
    this.append(form);
  }
}

const nativeRow = (label, value, unit = "") => {
  const row = document.createElement("div");
  row.innerText = `${label}: ${value}${unit ? ` ${unit}` : ""}`;
  return row;
};

const nativeHistoryCard = (title, entities, hours) => {
  const card = document.createElement("hui-history-graph-card");
  card.setConfig({ type: "history-graph", title, hours_to_show: hours, entities });
  return card;
};

class NerdminerCard extends HTMLElement {
  static getStubConfig() {
    return { title: "Nerdminer-HA", entity_prefix: "nm01", hours_to_show: 6 };
  }

  static getConfigElement() {
    return document.createElement("nerdminer-card-editor");
  }

  setConfig(config) {
    if (!config?.entity_prefix && !config?.entities) throw new Error("Set entity_prefix or entities");
    this.config = { title: "Nerdminer-HA", hours_to_show: 6, ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() { return 8; }

  _entity(key) {
    return this.config.entities?.[key] || `sensor.${this.config.entity_prefix}_${MINER_SUFFIXES[key]}`;
  }

  _state(key) {
    return this._hass.states[this._entity(key)];
  }

  _render() {
    if (!this._hass || !this.config) return;
    const root = this.shadowRoot || this.attachShadow({ mode: "open" });
    root.innerHTML = "";
    const card = document.createElement("ha-card");
    const content = document.createElement("div");
    const title = document.createElement("h2");
    title.innerText = this.config.title;
    content.append(title);
    content.append(nativeRow("Current hashrate", formatValue(this._state("current")?.state, 0), "kH/s"));
    content.append(nativeRow("1-minute average", formatValue(this._state("average_1m")?.state), "kH/s"));
    content.append(nativeRow("5-minute average", formatValue(this._state("average_5m")?.state), "kH/s"));
    content.append(nativeRow("Hardware / software", `${formatValue(this._state("hardware")?.state, 0)} / ${formatValue(this._state("software")?.state, 0)}`, "kH/s"));
    content.append(nativeRow("Shares accepted / rejected", `${formatValue(this._state("shares_accepted")?.state, 0)} / ${formatValue(this._state("shares_rejected")?.state, 0)}`));
    content.append(nativeRow("Board temperature", formatValue(this._state("temperature")?.state), "°C"));
    content.append(nativeRow("Uptime", formatValue(this._state("uptime")?.state), "h"));
    content.append(nativeRow("MAC address", this._state("mac")?.state || "-"));
    card.append(content);
    const history = nativeHistoryCard("Hashrate history", ["average_1m", "average_5m", "current", "hardware", "software"].map((key) => this._entity(key)), this.config.hours_to_show);
    history.hass = this._hass;
    card.append(history);
    root.append(card);
  }
}

class NerdminerFarmCard extends HTMLElement {
  static getStubConfig() {
    return { title: "Nerdminer farm", hours_to_show: 6 };
  }

  static getConfigElement() {
    return document.createElement("nerdminer-farm-card-editor");
  }

  setConfig(config) {
    this.config = { title: "Nerdminer farm", hours_to_show: 6, ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() { return 7; }

  _entities(suffix) {
    if (this.config.entities?.[suffix]) return this.config.entities[suffix];
    return Object.keys(this._hass.states).filter((entityId) => entityId.startsWith("sensor.") && entityId.endsWith(`_${MINER_SUFFIXES[suffix]}`));
  }

  _total(suffix) {
    return this._entities(suffix).reduce((total, entityId) => {
      const value = Number(this._hass.states[entityId]?.state);
      return Number.isFinite(value) ? total + value : total;
    }, 0);
  }

  _render() {
    if (!this._hass || !this.config) return;
    const root = this.shadowRoot || this.attachShadow({ mode: "open" });
    root.innerHTML = "";
    const card = document.createElement("ha-card");
    const content = document.createElement("div");
    const title = document.createElement("h2");
    title.innerText = this.config.title;
    content.append(title);
    const miners = new Set(this._entities("current").map((entityId) => entityId.replace(/^sensor\./, "").replace(/_current_hashrate$/, "")));
    content.append(nativeRow("Miners reporting", miners.size));
    content.append(nativeRow("Current hashrate", formatValue(this._total("current"), 0), "kH/s"));
    content.append(nativeRow("1-minute average", formatValue(this._total("average_1m")), "kH/s"));
    content.append(nativeRow("5-minute average", formatValue(this._total("average_5m")), "kH/s"));
    content.append(nativeRow("Hardware / software", `${formatValue(this._total("hardware"), 0)} / ${formatValue(this._total("software"), 0)}`, "kH/s"));
    content.append(nativeRow("Shares accepted / rejected", `${formatValue(this._total("shares_accepted"), 0)} / ${formatValue(this._total("shares_rejected"), 0)}`));
    content.append(nativeRow("Valid blocks", formatValue(this._total("valid_blocks"), 0)));
    card.append(content);
    const history = nativeHistoryCard("Farm hashrate history", [...this._entities("current"), ...this._entities("average_1m"), ...this._entities("average_5m")], this.config.hours_to_show);
    history.hass = this._hass;
    card.append(history);
    root.append(card);
  }
}

customElements.define("nerdminer-card", NerdminerCard);
customElements.define("nerdminer-farm-card", NerdminerFarmCard);
customElements.define("nerdminer-card-editor", NerdminerCardEditor);
customElements.define("nerdminer-farm-card-editor", NerdminerFarmCardEditor);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "nerdminer-card", name: "Nerdminer-HA", description: "Native per-miner telemetry and history",
  preview: true, documentationURL: "https://github.com/brian000/nerdminer-ha",
});
window.customCards.push({
  type: "nerdminer-farm-card", name: "Nerdminer farm", description: "Native aggregate stats for all Nerdminers",
  preview: true, documentationURL: "https://github.com/brian000/nerdminer-ha",
});
