"""HTML/CSS/JS fragment for fund OHLC + indicator modal (Lightweight Charts CDN).

Vendored from https://github.com/NicholasLina/seg-fund-scraper/blob/main/fund_chart_embed.py
so ``ia-funds email`` HTML matches the seg-fund-scraper fund analysis report (including
the chart modal shell; chart data may be empty for wide NAV-only exports).
"""

from __future__ import annotations


def build_chart_viewer_html(chart_json: str) -> str:
    """Insert before </body>. chart_json is a JSON object string.

    Escape ``<`` as ``\\u003c`` so a ``</script>`` substring inside string values
    cannot terminate the HTML ``<script>`` block early (browser HTML tokenizer).
    """
    safe = chart_json.replace("<", "\\u003c")
    # Split so chart_json is never parsed as part of this module's string endings.
    return CHART_PREFIX + safe + CHART_SUFFIX


CHART_PREFIX = r"""<style>
.chart-modal {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background: rgba(15, 41, 66, 0.5);
  -webkit-tap-highlight-color: transparent;
  overscroll-behavior: contain;
  touch-action: none;
}
.chart-modal.is-open { display: flex; }
.chart-modal-dialog {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 12px 48px rgba(15, 41, 66, 0.2);
  max-width: min(1400px, 98vw);
  width: 100%;
  max-height: min(94vh, 94dvh);
  overflow: auto;
  touch-action: pan-y;
  -webkit-overflow-scrolling: touch;
  display: flex;
  flex-direction: column;
  position: relative;
  isolation: isolate;
}
.chart-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid #d8dee9;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 50;
  box-shadow: 0 2px 10px rgba(15, 41, 66, 0.08);
}
.chart-modal-head h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 650;
  color: #1c2333;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chart-modal-close {
  border: none;
  background: #edf2f7;
  color: #1c2333;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  font-size: 1.4rem;
  line-height: 1;
  cursor: pointer;
  position: relative;
  z-index: 60;
  flex-shrink: 0;
}
.chart-modal-close:hover { background: #e2e8f0; }
.chart-modal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
  padding: 14px 16px 18px;
  position: relative;
  z-index: 1;
}
@media (max-width: 900px) {
  .chart-modal-grid { grid-template-columns: 1fr; }
}
.chart-stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
.chart-stack-h {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #5c6b7e;
  margin: 4px 0 2px;
}
.chart-pane-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: #2c5282;
}
.chart-pane-shell {
  position: relative;
  width: 100%;
}
.chart-pane-shell .chart-pane {
  width: 100%;
}
.chart-fs-toggle {
  position: absolute;
  top: 5px;
  right: 5px;
  z-index: 10;
  width: 30px;
  height: 30px;
  padding: 0;
  border: 1px solid #d8dee9;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  color: #2b6cb0;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(15, 41, 66, 0.12);
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.chart-fs-toggle:hover {
  background: #e8f1fc;
  border-color: #2b6cb0;
}
.chart-fs-toggle:focus-visible {
  outline: 2px solid #2b6cb0;
  outline-offset: 1px;
}
.chart-fs-toggle svg {
  display: block;
  pointer-events: none;
}
.chart-pane-shell .chart-fs-icon-out {
  display: none;
}
.chart-pane-shell:fullscreen,
.chart-pane-shell:-webkit-full-screen {
  display: flex;
  flex-direction: column;
  background: #fafbfd;
  padding: 8px;
  box-sizing: border-box;
}
.chart-pane-shell:fullscreen .chart-pane,
.chart-pane-shell:-webkit-full-screen .chart-pane {
  flex: 1;
  height: auto !important;
  min-height: 240px;
  width: 100%;
}
.chart-pane-shell:fullscreen .chart-fs-icon-in,
.chart-pane-shell:-webkit-full-screen .chart-fs-icon-in {
  display: none;
}
.chart-pane-shell:fullscreen .chart-fs-icon-out,
.chart-pane-shell:-webkit-full-screen .chart-fs-icon-out {
  display: block;
}
.chart-pane {
  width: 100%;
  height: 168px;
  min-height: 150px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  background: #fafbfd;
  position: relative;
  z-index: 1;
  isolation: isolate;
}
.chart-pane canvas {
  position: relative;
  z-index: 1;
}
td.chart-cell {
  text-align: center;
  width: 52px;
  vertical-align: middle;
}
.chart-open-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border: 1px solid #d8dee9;
  border-radius: 10px;
  background: #fff;
  color: #2b6cb0;
  cursor: pointer;
  line-height: 0;
  position: relative;
  z-index: 2;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}
.chart-open-btn svg {
  pointer-events: none;
  display: block;
}
.chart-open-btn:hover {
  background: #e8f1fc;
  border-color: #2b6cb0;
}
</style>
<div id="chart-modal" class="chart-modal" role="dialog" aria-modal="true" aria-hidden="true">
  <div class="chart-modal-dialog">
    <div class="chart-modal-head">
      <h2 id="chart-modal-title">Chart</h2>
      <button type="button" class="chart-modal-close" id="chart-modal-close" aria-label="Close">&times;</button>
    </div>
    <div class="chart-modal-grid">
      <div class="chart-stack">
        <div class="chart-stack-h">Monthly (up to 36 months)</div>
        <div class="chart-pane-title">Candlesticks (MA 20 / 40)</div>
        <div class="chart-pane-shell">
          <button type="button" class="chart-fs-toggle" aria-pressed="false" aria-label="Fullscreen chart" title="Fullscreen">
            <svg class="chart-fs-icon-in" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
            </svg>
            <svg class="chart-fs-icon-out" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
            </svg>
          </button>
          <div class="chart-pane" id="ch-m-c"></div>
        </div>
        <div class="chart-pane-title">MACD (12, 26, 9)</div>
        <div class="chart-pane-shell">
          <button type="button" class="chart-fs-toggle" aria-pressed="false" aria-label="Fullscreen chart" title="Fullscreen">
            <svg class="chart-fs-icon-in" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
            </svg>
            <svg class="chart-fs-icon-out" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
            </svg>
          </button>
          <div class="chart-pane" id="ch-m-macd"></div>
        </div>
        <div class="chart-pane-title">Stochastic (15, 5, 2) &amp; (5, 3, 2)</div>
        <div class="chart-pane-shell">
          <button type="button" class="chart-fs-toggle" aria-pressed="false" aria-label="Fullscreen chart" title="Fullscreen">
            <svg class="chart-fs-icon-in" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
            </svg>
            <svg class="chart-fs-icon-out" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
            </svg>
          </button>
          <div class="chart-pane" id="ch-m-stoch"></div>
        </div>
        <div class="chart-pane-title">RSI (14)</div>
        <div class="chart-pane-shell">
          <button type="button" class="chart-fs-toggle" aria-pressed="false" aria-label="Fullscreen chart" title="Fullscreen">
            <svg class="chart-fs-icon-in" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
            </svg>
            <svg class="chart-fs-icon-out" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
            </svg>
          </button>
          <div class="chart-pane" id="ch-m-rsi"></div>
        </div>
      </div>
      <div class="chart-stack">
        <div class="chart-stack-h">Weekly (up to 36 weeks)</div>
        <div class="chart-pane-title">Candlesticks (MA 20 / 40)</div>
        <div class="chart-pane-shell">
          <button type="button" class="chart-fs-toggle" aria-pressed="false" aria-label="Fullscreen chart" title="Fullscreen">
            <svg class="chart-fs-icon-in" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
            </svg>
            <svg class="chart-fs-icon-out" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
            </svg>
          </button>
          <div class="chart-pane" id="ch-w-c"></div>
        </div>
        <div class="chart-pane-title">MACD (12, 26, 9)</div>
        <div class="chart-pane-shell">
          <button type="button" class="chart-fs-toggle" aria-pressed="false" aria-label="Fullscreen chart" title="Fullscreen">
            <svg class="chart-fs-icon-in" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
            </svg>
            <svg class="chart-fs-icon-out" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
            </svg>
          </button>
          <div class="chart-pane" id="ch-w-macd"></div>
        </div>
        <div class="chart-pane-title">Stochastic (15, 5, 2) &amp; (5, 3, 2)</div>
        <div class="chart-pane-shell">
          <button type="button" class="chart-fs-toggle" aria-pressed="false" aria-label="Fullscreen chart" title="Fullscreen">
            <svg class="chart-fs-icon-in" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
            </svg>
            <svg class="chart-fs-icon-out" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
            </svg>
          </button>
          <div class="chart-pane" id="ch-w-stoch"></div>
        </div>
        <div class="chart-pane-title">RSI (14)</div>
        <div class="chart-pane-shell">
          <button type="button" class="chart-fs-toggle" aria-pressed="false" aria-label="Fullscreen chart" title="Fullscreen">
            <svg class="chart-fs-icon-in" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
            </svg>
            <svg class="chart-fs-icon-out" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
            </svg>
          </button>
          <div class="chart-pane" id="ch-w-rsi"></div>
        </div>
      </div>
    </div>
  </div>
</div>
<script type="application/json" id="fund-chart-data">"""

CHART_SUFFIX = r"""</script>
<!-- Load chart library synchronously so the init script always runs after LightweightCharts exists. -->
<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
<script>
(function () {
  var dataEl = document.getElementById("fund-chart-data");
  var modal = document.getElementById("chart-modal");
  var titleEl = document.getElementById("chart-modal-title");
  var closeBtn = document.getElementById("chart-modal-close");
  if (!dataEl || !modal || !titleEl || !closeBtn) return;

  var LC = typeof LightweightCharts !== "undefined" ? LightweightCharts : null;

  var FUND_CHART_DATA = {};
  try {
    FUND_CHART_DATA = JSON.parse(dataEl.textContent || "{}");
  } catch (e) {
    FUND_CHART_DATA = {};
  }

  var chartPairs = [];
  var bodyOverflowPrev = "";
  var htmlOverflowPrev = "";
  var lastChartTouchMs = 0;

  function lockPageScroll() {
    bodyOverflowPrev = document.body.style.overflow;
    htmlOverflowPrev = document.documentElement.style.overflow;
    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";
  }

  function unlockPageScroll() {
    document.body.style.overflow = bodyOverflowPrev;
    document.documentElement.style.overflow = htmlOverflowPrev;
  }
  function destroyCharts() {
    chartPairs.forEach(function (p) {
      try { p.chart.remove(); } catch (e1) {}
    });
    chartPairs = [];
  }
  function pushChart(el, chart) {
    if (el && chart) chartPairs.push({ el: el, chart: chart });
  }

  function baseOpts() {
    var cm = 1;
    if (LC && LC.CrosshairMode !== undefined) cm = LC.CrosshairMode.Normal;
    return {
      layout: {
        background: { type: "solid", color: "#fafbfd" },
        textColor: "#1c2333",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#e2e8f0" },
        horzLines: { color: "#e2e8f0" },
      },
      rightPriceScale: {
        borderColor: "#d8dee9",
        scaleMargins: { top: 0.12, bottom: 0.1 },
      },
      timeScale: {
        borderColor: "#d8dee9",
        rightOffset: 4,
        fixLeftEdge: false,
        fixRightEdge: false,
      },
      crosshair: { mode: cm },
    };
  }

  function paneSize(el) {
    var w = el.clientWidth || el.getBoundingClientRect().width || 400;
    var h = el.clientHeight || el.getBoundingClientRect().height || 168;
    return { width: Math.max(120, Math.floor(w)), height: Math.max(120, Math.floor(h)) };
  }

  function lineStyleSolid() {
    if (LC && LC.LineStyle !== undefined && LC.LineStyle.Solid !== undefined) {
      return LC.LineStyle.Solid;
    }
    return 0;
  }

  function lineStyleDashed() {
    if (LC && LC.LineStyle !== undefined && LC.LineStyle.Dashed !== undefined) {
      return LC.LineStyle.Dashed;
    }
    return 2;
  }

  function lineStyleDotted() {
    if (LC && LC.LineStyle !== undefined && LC.LineStyle.Dotted !== undefined) {
      return LC.LineStyle.Dotted;
    }
    return 1;
  }

  function findPivotHighs(candles) {
    var pivots = [];
    for (var i = 1; i < candles.length - 1; i++) {
      if (candles[i].high > candles[i - 1].high && candles[i].high > candles[i + 1].high) {
        pivots.push({ idx: i, val: candles[i].high });
      }
    }
    return pivots;
  }

  function findPivotLows(candles) {
    var pivots = [];
    for (var i = 1; i < candles.length - 1; i++) {
      if (candles[i].low < candles[i - 1].low && candles[i].low < candles[i + 1].low) {
        pivots.push({ idx: i, val: candles[i].low });
      }
    }
    return pivots;
  }

  function extendTrendFromPivots(candles, i0, v0, i1, v1) {
    if (i0 === i1) return [];
    var pts = [];
    var slope = (v1 - v0) / (i1 - i0);
    for (var k = i0; k < candles.length; k++) {
      pts.push({ time: candles[k].time, value: v0 + slope * (k - i0) });
    }
    return pts;
  }

  function addCandleTrendlines(chart, candles) {
    if (!candles || candles.length < 5) return;
    var solid = lineStyleSolid();
    var ph = findPivotHighs(candles);
    if (ph.length >= 2) {
      var H0 = ph[ph.length - 2];
      var H1 = ph[ph.length - 1];
      if (H1.idx > H0.idx && H1.val < H0.val) {
        var resPts = extendTrendFromPivots(candles, H0.idx, H0.val, H1.idx, H1.val);
        if (resPts.length) {
          var res = chart.addLineSeries({
            color: "rgba(220, 38, 38, 0.85)",
            lineWidth: 2,
            lineStyle: solid,
            title: "Resistance",
            priceLineVisible: false,
            lastValueVisible: false,
          });
          res.setData(resPts);
        }
      }
    }
    var pl = findPivotLows(candles);
    if (pl.length >= 2) {
      var L0 = pl[pl.length - 2];
      var L1 = pl[pl.length - 1];
      if (L1.idx > L0.idx && L1.val > L0.val) {
        var supPts = extendTrendFromPivots(candles, L0.idx, L0.val, L1.idx, L1.val);
        if (supPts.length) {
          var sup = chart.addLineSeries({
            color: "rgba(22, 163, 74, 0.85)",
            lineWidth: 2,
            lineStyle: solid,
            title: "Support",
            priceLineVisible: false,
            lastValueVisible: false,
          });
          sup.setData(supPts);
        }
      }
    }
  }

  function mountCandles(el, side) {
    if (!LC || !el || !side) return;
    var rows = side.candle || [];
    if (!rows.length) return;
    var sz = paneSize(el);
    var chart = LC.createChart(el, Object.assign(sz, baseOpts()));
    var s = chart.addCandlestickSeries({
      upColor: "#2f855a",
      downColor: "#c53030",
      borderUpColor: "#2f855a",
      borderDownColor: "#c53030",
      wickUpColor: "#2f855a",
      wickDownColor: "#c53030",
    });
    s.setData(rows);
    var dot = lineStyleDotted();
    if (side.sma_20 && side.sma_20.length) {
      var m20 = chart.addLineSeries({
        color: "#2563eb",
        lineWidth: 1,
        lineStyle: dot,
        title: "MA 20",
        priceLineVisible: false,
        lastValueVisible: true,
      });
      m20.setData(side.sma_20);
    }
    if (side.sma_40 && side.sma_40.length) {
      var m40 = chart.addLineSeries({
        color: "#b45309",
        lineWidth: 1.5,
        title: "MA 40",
        priceLineVisible: false,
        lastValueVisible: true,
      });
      m40.setData(side.sma_40);
    }
    addCandleTrendlines(chart, rows);
    chart.timeScale().fitContent();
    pushChart(el, chart);
  }

  function mountMacd(el, side) {
    if (!LC || !el || !side) return;
    var sz = paneSize(el);
    var chart = LC.createChart(el, Object.assign(sz, baseOpts()));
    var a = chart.addLineSeries({ color: "#2962FF", lineWidth: 2, title: "MACD" });
    var b = chart.addLineSeries({ color: "#FF6D00", lineWidth: 2, title: "Signal" });
    a.setData(side.macd_main || []);
    b.setData(side.macd_signal || []);
    try {
      a.createPriceLine({
        price: 0,
        color: "rgba(55, 65, 81, 0.65)",
        lineWidth: 1,
        lineStyle: lineStyleDashed(),
        axisLabelVisible: true,
      });
    } catch (eZ) {}
    chart.timeScale().fitContent();
    pushChart(el, chart);
  }

  function mountRsi(el, side) {
    if (!LC || !el || !side) return;
    var sz = paneSize(el);
    var chart = LC.createChart(el, Object.assign(sz, baseOpts()));
    var s = chart.addLineSeries({ color: "#9d174d", lineWidth: 2, title: "RSI (14)" });
    s.setData(side.rsi || []);
    var dash = lineStyleDashed();
    var guide = "rgba(55, 65, 81, 0.7)";
    try {
      s.createPriceLine({
        price: 40,
        color: guide,
        lineWidth: 1,
        lineStyle: dash,
        axisLabelVisible: true,
      });
      s.createPriceLine({
        price: 60,
        color: guide,
        lineWidth: 1,
        lineStyle: dash,
        axisLabelVisible: true,
      });
    } catch (eR) {}
    chart.timeScale().fitContent();
    pushChart(el, chart);
  }

  function stochPalette(kind) {
    if (kind === "s5") {
      return { k: "#dc2626", d: "#f87171" };
    }
    return { k: "#1d4ed8", d: "#60a5fa" };
  }

  function mountStochCombined(el, side) {
    if (!LC || !el || !side) return;
    var sz = paneSize(el);
    var chart = LC.createChart(el, Object.assign(sz, baseOpts()));
    var dotted = lineStyleDotted();
    var pal15 = stochPalette("s15");
    var pal5 = stochPalette("s5");
    var k15 = chart.addLineSeries({
      color: pal15.k,
      lineWidth: 2.75,
      title: "(15,5,2) %K",
    });
    var d15 = chart.addLineSeries({
      color: pal15.d,
      lineWidth: 1,
      lineStyle: dotted,
      title: "(15,5,2) %D",
    });
    var k5 = chart.addLineSeries({
      color: pal5.k,
      lineWidth: 2.75,
      title: "(5,3,2) %K",
    });
    var d5 = chart.addLineSeries({
      color: pal5.d,
      lineWidth: 1,
      lineStyle: dotted,
      title: "(5,3,2) %D",
    });
    k15.setData(side.stoch1555_k || []);
    d15.setData(side.stoch1555_d || []);
    k5.setData(side.stoch533_k || []);
    d5.setData(side.stoch533_d || []);
    var dash = lineStyleDashed();
    var sg = "rgba(55, 65, 81, 0.75)";
    try {
      k15.createPriceLine({
        price: 20,
        color: sg,
        lineWidth: 1,
        lineStyle: dash,
        axisLabelVisible: true,
        title: "20",
      });
      k15.createPriceLine({
        price: 80,
        color: sg,
        lineWidth: 1,
        lineStyle: dash,
        axisLabelVisible: true,
        title: "80",
      });
    } catch (eS) {}
    chart.timeScale().fitContent();
    pushChart(el, chart);
  }

  function resizeCharts() {
    chartPairs.forEach(function (p) {
      try {
        var sz = paneSize(p.el);
        p.chart.applyOptions({ width: sz.width, height: sz.height });
        p.chart.timeScale().fitContent();
      } catch (e2) {}
    });
  }

  function fullscreenEl() {
    return document.fullscreenElement || document.webkitFullscreenElement;
  }

  function exitFullscreenInsideModal() {
    var fs = fullscreenEl();
    if (!fs || !modal.contains(fs)) return;
    try {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      }
    } catch (e) {}
  }

  function requestPaneFullscreen(shell) {
    if (!shell) return;
    function afterSize() {
      resizeCharts();
      requestAnimationFrame(function () {
        resizeCharts();
      });
    }
    if (shell.requestFullscreen) {
      var p = shell.requestFullscreen();
      if (p && typeof p.then === "function") {
        p.then(afterSize).catch(function () {});
      } else {
        afterSize();
      }
      return;
    }
    if (shell.webkitRequestFullscreen) {
      try {
        shell.webkitRequestFullscreen();
        afterSize();
      } catch (e) {}
    }
  }

  function syncFullscreenToggleAria() {
    modal.querySelectorAll(".chart-pane-shell").forEach(function (shell) {
      var btn = shell.querySelector(".chart-fs-toggle");
      if (!btn) return;
      var fs = fullscreenEl() === shell;
      btn.setAttribute("aria-pressed", fs ? "true" : "false");
      btn.setAttribute("aria-label", fs ? "Exit fullscreen" : "Fullscreen chart");
      btn.title = fs ? "Exit fullscreen" : "Fullscreen";
    });
  }

  function mountAllCharts(fund) {
    if (!LC) return;
    mountCandles(document.getElementById("ch-m-c"), fund.monthly);
    mountMacd(document.getElementById("ch-m-macd"), fund.monthly);
    mountStochCombined(document.getElementById("ch-m-stoch"), fund.monthly);
    mountRsi(document.getElementById("ch-m-rsi"), fund.monthly);
    mountCandles(document.getElementById("ch-w-c"), fund.weekly);
    mountMacd(document.getElementById("ch-w-macd"), fund.weekly);
    mountStochCombined(document.getElementById("ch-w-stoch"), fund.weekly);
    mountRsi(document.getElementById("ch-w-rsi"), fund.weekly);
    resizeCharts();
    modal.querySelectorAll(".chart-pane canvas").forEach(function (c) {
      c.setAttribute("tabindex", "-1");
    });
  }

  function scheduleMountCharts(fund) {
    if (!LC) return;
    function run() {
      mountAllCharts(fund);
      resizeCharts();
      requestAnimationFrame(function () {
        resizeCharts();
      });
    }
    requestAnimationFrame(function () {
      requestAnimationFrame(run);
    });
  }

  function openModal(key) {
    var fund = FUND_CHART_DATA[key];
    destroyCharts();
    if (!fund) {
      titleEl.textContent = "No chart data for this row.";
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
      lockPageScroll();
      return;
    }
    titleEl.textContent = fund.title || key;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    lockPageScroll();
    if (!LC) {
      titleEl.textContent =
        (fund.title || key) + " — chart library failed to load (check network / ad blocker).";
      return;
    }
    scheduleMountCharts(fund);
  }

  function closeModal() {
    exitFullscreenInsideModal();
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    destroyCharts();
    unlockPageScroll();
  }

  function openFromChartButton(btn) {
    if (!btn) return;
    var k = btn.getAttribute("data-chart-key");
    if (k) openModal(k);
  }

  document.addEventListener(
    "touchend",
    function (ev) {
      var t = ev.target;
      if (!t || !t.closest) return;
      var btn = t.closest(".chart-open-btn");
      if (!btn) return;
      ev.preventDefault();
      lastChartTouchMs = Date.now();
      openFromChartButton(btn);
    },
    { capture: true, passive: false }
  );

  document.addEventListener("click", function (ev) {
    var t = ev.target;
    if (!t || !t.closest) return;
    var fsToggle = t.closest(".chart-fs-toggle");
    if (fsToggle && modal.contains(fsToggle)) {
      ev.preventDefault();
      ev.stopPropagation();
      var shell = fsToggle.closest(".chart-pane-shell");
      if (!shell) return;
      if (fullscreenEl() === shell) {
        exitFullscreenInsideModal();
      } else {
        requestPaneFullscreen(shell);
      }
      syncFullscreenToggleAria();
      return;
    }
    if (Date.now() - lastChartTouchMs < 450) {
      var dup = t.closest(".chart-open-btn");
      if (dup) {
        ev.preventDefault();
        ev.stopPropagation();
        return;
      }
    }
    var btn = t.closest(".chart-open-btn");
    if (btn) {
      ev.preventDefault();
      openFromChartButton(btn);
      return;
    }
    if (modal.classList.contains("is-open") && t === modal) closeModal();
  }, true);

  closeBtn.addEventListener(
    "click",
    function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      closeModal();
    },
    true
  );
  closeBtn.addEventListener(
    "mousedown",
    function (ev) {
      ev.stopPropagation();
    },
    true
  );

  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Escape" || !modal.classList.contains("is-open")) return;
    var fs = fullscreenEl();
    if (fs && modal.contains(fs)) {
      exitFullscreenInsideModal();
      syncFullscreenToggleAria();
      return;
    }
    closeModal();
  });

  function onFullscreenViewportChange() {
    if (!modal.classList.contains("is-open")) return;
    syncFullscreenToggleAria();
    resizeCharts();
    requestAnimationFrame(function () {
      resizeCharts();
    });
  }
  document.addEventListener("fullscreenchange", onFullscreenViewportChange);
  document.addEventListener("webkitfullscreenchange", onFullscreenViewportChange);

  window.addEventListener("resize", function () {
    if (modal.classList.contains("is-open")) resizeCharts();
  });
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", function () {
      if (modal.classList.contains("is-open")) resizeCharts();
    });
  }
})();
</script>
"""
