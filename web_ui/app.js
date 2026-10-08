/**
 * ShyamEdge Pro Institutional Trading Terminal Engine
 * High-performance ES6 Client Architecture with Zero-Lag Reactivity
 */

const STATE = {
    symbol: "NIFTY50",
    direction: "CE",
    timeframe: "5m",
    journalFilter: "today",
    journalDate: null,
    lotSizes: { NIFTY50: 75, SENSEX: 20 },
    chartData: null,
    strategiesList: [],
    pollingTimer: null
};

// Utilities
function showToast(message, type = "normal") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type === "success" ? "toast-success" : type === "error" ? "toast-error" : ""}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function formatINR(val, plusSign = false) {
    if (val === undefined || val === null || isNaN(val)) return "₹0.00";
    const num = Number(val);
    const sign = plusSign && num > 0 ? "+" : "";
    return `${sign}₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// -------------------------------------------------------------
// INITIALIZATION
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    initEventListeners();
    fetchMarketStatus();
    fetchPortfolioState();
    fetchChartData();
    fetchTradesJournal();
    fetchStrategies();
    fetchEquityCurve();

    // Fast polling loop: 1s for status & clock, 2s for position & portfolio
    setInterval(fetchMarketStatus, 1000);
    setInterval(fetchPortfolioState, 2000);
});

// -------------------------------------------------------------
// EVENT LISTENERS
// -------------------------------------------------------------
function initEventListeners() {
    // Underlying Selector (NIFTY vs SENSEX)
    document.getElementById("btn-sel-nifty").addEventListener("click", () => switchUnderlying("NIFTY50"));
    document.getElementById("btn-sel-sensex").addEventListener("click", () => switchUnderlying("SENSEX"));

    // Call / Put Toggle
    document.getElementById("btn-dir-ce").addEventListener("click", () => switchDirection("CE"));
    document.getElementById("btn-dir-pe").addEventListener("click", () => switchDirection("PE"));

    // Strike Select change
    document.getElementById("strike-select").addEventListener("change", updateTicketCalculations);

    // Order Execution
    document.getElementById("btn-place-order").addEventListener("click", executePaperOrder);

    // Square-off active position
    document.getElementById("btn-square-off-pos").addEventListener("click", squareOffActivePosition);

    // Presets on Empty Pos Card
    document.getElementById("btn-quick-nifty-ce").addEventListener("click", () => {
        switchUnderlying("NIFTY50");
        switchDirection("CE");
        executePaperOrder();
    });
    document.getElementById("btn-quick-sensex-ce").addEventListener("click", () => {
        switchUnderlying("SENSEX");
        switchDirection("CE");
        executePaperOrder();
    });

    // Kill switch
    document.getElementById("btn-kill-switch").addEventListener("click", () => {
        if (confirm("EMERGENCY KILL SWITCH: Are you sure you want to disarm desk and liquidate all active positions?")) {
            squareOffActivePosition();
            showToast("🛑 DESK DISARMED: Position liquidated to flat cash.", "error");
        }
    });

    // DB Maintenance
    document.getElementById("btn-clear-pos").addEventListener("click", async () => {
        const res = await fetch("/api/db/clear-position", { method: "POST" });
        const data = await res.json();
        showToast(data.message, "success");
        fetchPortfolioState();
    });

    document.getElementById("btn-sync-bench").addEventListener("click", async () => {
        showToast("Syncing 73 benchmark trades...", "normal");
        const res = await fetch("/api/db/sync-benchmark", { method: "POST" });
        const data = await res.json();
        showToast(data.message, "success");
        fetchPortfolioState();
        fetchTradesJournal();
        fetchStrategies();
        fetchEquityCurve();
    });

    document.getElementById("btn-factory-reset").addEventListener("click", async () => {
        if (confirm("FACTORY RESET: Wipe all trades, orders, and positions to 0?")) {
            const res = await fetch("/api/db/factory-reset", { method: "POST" });
            const data = await res.json();
            showToast(data.message, "error");
            fetchPortfolioState();
            fetchTradesJournal();
            fetchStrategies();
            fetchEquityCurve();
        }
    });

    // Tab Navigation
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const tabId = btn.getAttribute("data-tab");
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(tabId).classList.add("active");

            // Trigger redraw on newly active charts
            if (tabId === "tab-chart") renderPlotlyCandlestick();
            if (tabId === "tab-journal") renderPlotlyWaterfall();
            if (tabId === "tab-matrix") renderPlotlyStrategyPnl();
            if (tabId === "tab-equity") renderPlotlyEquityCurve();
        });
    });

    // Timeframe Pills
    document.querySelectorAll(".tf-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tf-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            STATE.timeframe = btn.getAttribute("data-tf");
            fetchChartData();
        });
    });

    // Journal Filters
    document.getElementById("btn-journal-today").addEventListener("click", () => {
        document.getElementById("btn-journal-today").classList.add("active");
        document.getElementById("btn-journal-all").classList.remove("active");
        STATE.journalFilter = "today";
        fetchTradesJournal();
    });

    document.getElementById("btn-journal-all").addEventListener("click", () => {
        document.getElementById("btn-journal-all").classList.add("active");
        document.getElementById("btn-journal-today").classList.remove("active");
        STATE.journalFilter = "all";
        fetchTradesJournal();
    });

    document.getElementById("select-journal-date").addEventListener("change", (e) => {
        STATE.journalFilter = e.target.value;
        document.getElementById("btn-journal-today").classList.remove("active");
        document.getElementById("btn-journal-all").classList.remove("active");
        fetchTradesJournal();
    });

    // Strategy Inspector dropdown
    document.getElementById("select-inspect-strat").addEventListener("change", (e) => {
        renderStrategyInspector(e.target.value);
    });

    // Manual Refresh
    document.getElementById("btn-manual-refresh").addEventListener("click", () => {
        fetchMarketStatus();
        fetchPortfolioState();
        fetchChartData();
        fetchTradesJournal();
        showToast("Market data refreshed.", "normal");
    });
}

function switchUnderlying(sym) {
    STATE.symbol = sym;
    document.getElementById("btn-sel-nifty").classList.toggle("active", sym === "NIFTY50");
    document.getElementById("btn-sel-sensex").classList.toggle("active", sym === "SENSEX");
    
    // Update strikes list
    const select = document.getElementById("strike-select");
    select.innerHTML = "";
    if (sym === "NIFTY50") {
        select.innerHTML = `
            <option value="24500" data-delta="0.50">24500 ATM (Δ 0.50)</option>
            <option value="24450" data-delta="0.60">24450 ITM-1 (Δ 0.60)</option>
            <option value="24400" data-delta="0.70">24400 ITM-2 (Δ 0.70)</option>
            <option value="24550" data-delta="0.40">24550 OTM-1 (Δ 0.40)</option>
        `;
    } else {
        select.innerHTML = `
            <option value="81100" data-delta="0.50">81100 ATM (Δ 0.50)</option>
            <option value="81000" data-delta="0.60">81000 ITM-1 (Δ 0.60)</option>
            <option value="80900" data-delta="0.70">80900 ITM-2 (Δ 0.70)</option>
            <option value="81200" data-delta="0.40">81200 OTM-1 (Δ 0.40)</option>
        `;
    }
    updateTicketCalculations();
    fetchChartData();
}

function switchDirection(dir) {
    STATE.direction = dir;
    document.getElementById("btn-dir-ce").classList.toggle("active", dir === "CE");
    document.getElementById("btn-dir-pe").classList.toggle("active", dir === "PE");
    updateTicketCalculations();
}

function updateTicketCalculations() {
    const sym = STATE.symbol;
    const lot = STATE.lotSizes[sym];
    const premium = sym === "NIFTY50" ? 142.50 : 320.00;
    const margin = premium * lot;
    const sl = (premium * 0.85).toFixed(2);
    const tgt = (premium * 1.30).toFixed(2);

    document.getElementById("ticket-lot-display").textContent = `${lot} Qty (1 Lot)`;
    document.getElementById("ticket-premium-display").textContent = `₹${premium.toFixed(2)}`;
    document.getElementById("ticket-margin-display").textContent = formatINR(margin);
    document.getElementById("ticket-sl-display").textContent = `₹${sl}`;
    document.getElementById("ticket-tgt-display").textContent = `₹${tgt}`;
}

// -------------------------------------------------------------
// DATA FETCHERS
// -------------------------------------------------------------

async function fetchMarketStatus() {
    try {
        const res = await fetch("/api/market-status");
        const data = await res.json();

        document.getElementById("ist-clock").textContent = `${data.ist_time} IST`;
        document.getElementById("session-status-text").textContent = data.session_label;

        // Update Tickers
        if (data.tickers) {
            document.getElementById("nifty-spot").textContent = data.tickers.NIFTY50.price.toFixed(2);
            document.getElementById("sensex-spot").textContent = data.tickers.SENSEX.price.toFixed(2);
            document.getElementById("banknifty-spot").textContent = data.tickers.BANKNIFTY.price.toFixed(2);
            document.getElementById("vix-spot").textContent = data.tickers.INDIAVIX.price.toFixed(2);
        }
    } catch (e) {
        console.error("Market status fetch error:", e);
    }
}

async function fetchPortfolioState() {
    try {
        const res = await fetch(`/api/portfolio-state?underlying_filter=${STATE.symbol}`);
        const data = await res.json();

        // Top KPIs
        document.getElementById("kpi-account-equity").textContent = formatINR(data.account_equity);
        document.getElementById("kpi-equity-delta").textContent = `+${data.return_on_capital_pct}% on Capital`;
        document.getElementById("kpi-net-pnl").textContent = formatINR(data.realized_net_pnl, true);
        document.getElementById("kpi-win-rate").textContent = `${data.win_rate_pct}% Win Rate (${data.winning_trades}W / ${data.losing_trades}L)`;
        document.getElementById("kpi-profit-factor").textContent = data.profit_factor.toFixed(2);
        document.getElementById("kpi-max-drawdown").textContent = `${data.max_drawdown_pct.toFixed(2)}%`;

        // Active Position Desk
        const activeView = document.getElementById("pos-active-view");
        const emptyView = document.getElementById("pos-empty-view");
        const posBadge = document.getElementById("pos-status-badge");
        const kpiMtm = document.getElementById("kpi-running-mtm");
        const kpiPosStatus = document.getElementById("kpi-pos-status");

        if (data.has_open_position && data.open_position) {
            const pos = data.open_position;
            activeView.classList.remove("hidden");
            emptyView.classList.add("hidden");

            posBadge.textContent = "ACTIVE LONG";
            posBadge.className = "pos-badge badge-pos";

            kpiMtm.textContent = formatINR(pos.unrealized_pnl, true);
            kpiMtm.className = `kpi-val font-mono ${pos.unrealized_pnl >= 0 ? "color-pos" : "color-neg"}`;
            kpiPosStatus.textContent = `${pos.option_symbol} (${pos.quantity} QTY)`;

            document.getElementById("pos-symbol").textContent = pos.option_symbol;
            document.getElementById("pos-qty").textContent = `${pos.quantity} QTY (1 Lot)`;
            document.getElementById("pos-mtm-display").textContent = formatINR(pos.unrealized_pnl, true);
            document.getElementById("pos-mtm-display").className = `mtm-amount ${pos.unrealized_pnl >= 0 ? "color-pos" : "color-neg"}`;
            document.getElementById("pos-return-display").textContent = `${pos.return_pct >= 0 ? "+" : ""}${pos.return_pct.toFixed(2)}%`;

            // Progress bar
            const entryP = pos.entry_price;
            const curP = pos.current_price;
            const slP = pos.stop_loss;
            const tgtP = pos.target;

            document.getElementById("pos-entry-price").textContent = `₹${entryP.toFixed(2)}`;
            document.getElementById("pos-current-price").textContent = `₹${curP.toFixed(2)}`;
            document.getElementById("pos-sl-val").textContent = `SL: ₹${slP.toFixed(2)}`;
            document.getElementById("pos-cur-val").textContent = `CMP: ₹${curP.toFixed(2)}`;
            document.getElementById("pos-tgt-val").textContent = `TGT: ₹${tgtP.toFixed(2)}`;

            let pct = ((curP - slP) / (tgtP - slP)) * 100;
            pct = Math.max(5, Math.min(100, pct));
            document.getElementById("pos-progress-fill").style.width = `${pct}%`;

            // Trailing Stop Ratchet status
            let trailLabel = "Initial Stop Loss Active (-15%)";
            if (pos.trailing_sl) {
                if (pos.trailing_sl >= entryP * 1.15) trailLabel = `🚀 Momentum Locked @ ₹${pos.trailing_sl.toFixed(2)} (+16%)`;
                else if (pos.trailing_sl >= entryP * 1.05) trailLabel = `⭐ Profit Locked @ ₹${pos.trailing_sl.toFixed(2)} (+8%)`;
                else if (pos.trailing_sl >= entryP) trailLabel = `🛡️ Breakeven Protected @ ₹${pos.trailing_sl.toFixed(2)} (0 Risk)`;
            }
            document.getElementById("pos-trailing-label").textContent = trailLabel;

            if (pos.greeks) {
                document.getElementById("pos-delta-val").textContent = pos.greeks.delta;
                document.getElementById("pos-theta-val").textContent = pos.greeks.theta;
            }
        } else {
            activeView.classList.add("hidden");
            emptyView.classList.remove("hidden");
            posBadge.textContent = "FLAT";
            posBadge.className = "pos-badge";
            kpiMtm.textContent = "₹0.00";
            kpiMtm.className = "kpi-val font-mono";
            kpiPosStatus.textContent = "FLAT CASH";
        }
    } catch (e) {
        console.error("Portfolio state fetch error:", e);
    }
}

async function fetchChartData() {
    try {
        const res = await fetch(`/api/chart-data?symbol=${STATE.symbol}&days=3`);
        STATE.chartData = await res.json();
        document.getElementById("chart-symbol-header").textContent = `${STATE.chartData.symbol} • ${STATE.timeframe.toUpperCase()} INTRADAY`;
        renderPlotlyCandlestick();
    } catch (e) {
        console.error("Chart data fetch error:", e);
    }
}

function renderPlotlyCandlestick() {
    if (!STATE.chartData || !STATE.chartData.candles || STATE.chartData.candles.length === 0) return;

    const cd = STATE.chartData;
    const times = cd.candles.map(c => c.time);
    const opens = cd.candles.map(c => c.open);
    const highs = cd.candles.map(c => c.high);
    const lows = cd.candles.map(c => c.low);
    const closes = cd.candles.map(c => c.close);
    const volumes = cd.volume.map(v => v.volume);
    const volColors = cd.volume.map(v => v.is_up ? "#10B981" : "#F43F5E");

    const vwapVals = cd.vwap.map(v => v.val);
    const ema20Vals = cd.ema20.map(v => v.val);
    const ema50Vals = cd.ema50.map(v => v.val);

    const candleTrace = {
        x: times,
        open: opens,
        high: highs,
        low: lows,
        close: closes,
        type: 'candlestick',
        name: cd.symbol,
        increasing: { line: { color: '#10B981', width: 1.5 }, fillcolor: '#10B981' },
        decreasing: { line: { color: '#F43F5E', width: 1.5 }, fillcolor: '#F43F5E' },
        xaxis: 'x',
        yaxis: 'y'
    };

    const vwapTrace = {
        x: times,
        y: vwapVals,
        type: 'scatter',
        mode: 'lines',
        name: 'VWAP',
        line: { color: '#06B6D4', width: 2 },
        xaxis: 'x',
        yaxis: 'y'
    };

    const ema20Trace = {
        x: times,
        y: ema20Vals,
        type: 'scatter',
        mode: 'lines',
        name: '20 EMA',
        line: { color: '#F59E0B', width: 1.5 },
        xaxis: 'x',
        yaxis: 'y'
    };

    const ema50Trace = {
        x: times,
        y: ema50Vals,
        type: 'scatter',
        mode: 'lines',
        name: '50 EMA',
        line: { color: '#A855F7', width: 1.5 },
        xaxis: 'x',
        yaxis: 'y'
    };

    const volTrace = {
        x: times,
        y: volumes,
        type: 'bar',
        name: 'Volume',
        marker: { color: volColors, opacity: 0.75 },
        xaxis: 'x',
        yaxis: 'y2'
    };

    const layout = {
        template: 'plotly_dark',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { l: 45, r: 20, t: 15, b: 30 },
        height: 480,
        showlegend: false,
        xaxis: {
            rangeslider: { visible: false },
            gridcolor: 'rgba(255,255,255,0.04)',
            linecolor: 'rgba(255,255,255,0.1)'
        },
        yaxis: {
            domain: [0.25, 1.0],
            gridcolor: 'rgba(255,255,255,0.04)',
            linecolor: 'rgba(255,255,255,0.1)'
        },
        yaxis2: {
            domain: [0.0, 0.20],
            gridcolor: 'rgba(255,255,255,0.03)',
            showticklabels: false
        }
    };

    Plotly.react('plotly-candlestick-chart', [candleTrace, vwapTrace, ema20Trace, ema50Trace, volTrace], layout, { responsive: true, displayModeBar: false });
}

// -------------------------------------------------------------
// TAB 2: DAY-BY-DAY TRADE JOURNAL
// -------------------------------------------------------------
let cachedJournalData = null;

async function fetchTradesJournal() {
    try {
        const res = await fetch(`/api/trades?date_filter=${STATE.journalFilter}&underlying_filter=${STATE.symbol}`);
        cachedJournalData = await res.json();
        renderJournalUI();
    } catch (e) {
        console.error("Trades journal fetch error:", e);
    }
}

function renderJournalUI() {
    if (!cachedJournalData) return;
    const jd = cachedJournalData;

    // Populate date picker
    const dateSelect = document.getElementById("select-journal-date");
    dateSelect.innerHTML = "";
    jd.available_dates.forEach(d => {
        const opt = document.createElement("option");
        opt.value = d;
        opt.textContent = d;
        if (d === jd.selected_date) opt.selected = true;
        dateSelect.appendChild(opt);
    });

    // Day KPIs
    const sm = jd.summary;
    document.getElementById("jm-trades").textContent = `${sm.count} (${sm.wins}W / ${sm.losses}L • ${sm.win_rate_pct}%)`;
    document.getElementById("jm-gross").textContent = formatINR(sm.gross_pnl, true);
    document.getElementById("jm-drag").textContent = formatINR(sm.total_drag);
    document.getElementById("jm-net").textContent = formatINR(sm.net_pnl, true);
    document.getElementById("jm-net").className = `dm-val font-mono ${sm.net_pnl >= 0 ? "color-pos" : "color-neg"}`;

    document.getElementById("journal-table-title").textContent = `EXECUTED TRADES LOG • ${jd.filter_label.toUpperCase()} (${sm.count} TRADES)`;

    // Trades Table
    const tbody = document.getElementById("journal-table-body");
    tbody.innerHTML = "";
    if (jd.trades.length === 0) {
        tbody.innerHTML = `<tr><td colspan="12" class="text-center" style="padding: 24px; color: #64748B;">No trades recorded for this session filter.</td></tr>`;
    } else {
        jd.trades.forEach(t => {
            const tr = document.createElement("tr");
            const exitTime = t.exit_time ? t.exit_time.split("T")[1] ? t.exit_time.split("T")[1].substring(0, 8) : t.exit_time.substring(11, 19) : "--";
            tr.innerHTML = `
                <td>${exitTime}</td>
                <td><span class="badge-pos" style="background: rgba(37,99,235,0.15); color: #60A5FA;">${t.strategy_id}</span></td>
                <td><strong>${t.underlying}</strong></td>
                <td>${t.option_symbol}</td>
                <td>${t.quantity}</td>
                <td>₹${t.entry_price.toFixed(2)}</td>
                <td>₹${t.exit_price.toFixed(2)}</td>
                <td>${formatINR(t.gross_pnl, true)}</td>
                <td class="color-amber">₹${(t.total_charges + t.slippage).toFixed(2)}</td>
                <td class="${t.net_pnl >= 0 ? 'color-pos' : 'color-neg'}"><strong>${formatINR(t.net_pnl, true)}</strong></td>
                <td class="${t.return_pct >= 0 ? 'color-pos' : 'color-neg'}">${t.return_pct >= 0 ? '+' : ''}${t.return_pct.toFixed(2)}%</td>
                <td><span class="${t.net_pnl >= 0 ? 'badge-pos' : 'badge-neg'}">${t.exit_reason}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Daily Calendar Table
    const calBody = document.getElementById("daily-calendar-body");
    calBody.innerHTML = "";
    jd.daily_calendar.forEach(dc => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${dc.date}</td>
            <td>${dc.trades}</td>
            <td>${dc.win_loss}</td>
            <td>${dc.win_rate}</td>
            <td class="${dc.is_green ? 'color-pos' : 'color-neg'}"><strong>${formatINR(dc.net_pnl, true)}</strong></td>
        `;
        calBody.appendChild(tr);
    });

    renderPlotlyWaterfall();
}

function renderPlotlyWaterfall() {
    if (!cachedJournalData || !cachedJournalData.daily_calendar) return;
    const items = [...cachedJournalData.daily_calendar].reverse();
    const dates = items.map(d => d.date);
    const pnls = items.map(d => d.net_pnl);
    const colors = items.map(d => d.is_green ? "#10B981" : "#F43F5E");

    const trace = {
        x: dates,
        y: pnls,
        type: 'bar',
        marker: { color: colors },
        text: pnls.map(p => formatINR(p, true)),
        textposition: 'outside'
    };

    const layout = {
        template: 'plotly_dark',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { l: 45, r: 20, t: 25, b: 35 },
        height: 300,
        xaxis: { gridcolor: 'rgba(255,255,255,0.04)' },
        yaxis: { gridcolor: 'rgba(255,255,255,0.04)' }
    };

    Plotly.react('plotly-waterfall-chart', [trace], layout, { responsive: true, displayModeBar: false });
}

// -------------------------------------------------------------
// TAB 3: 15 STRATEGIES ALPHA MATRIX
// -------------------------------------------------------------
let cachedStrategiesData = null;

async function fetchStrategies() {
    try {
        const res = await fetch(`/api/strategies?underlying_filter=${STATE.symbol}`);
        cachedStrategiesData = await res.json();
        renderStrategiesUI();
    } catch (e) {
        console.error("Strategies fetch error:", e);
    }
}

function renderStrategiesUI() {
    if (!cachedStrategiesData) return;
    const strats = cachedStrategiesData.strategies;

    // Populate inspector select
    const inspectSelect = document.getElementById("select-inspect-strat");
    inspectSelect.innerHTML = "";
    strats.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = `${s.id} - ${s.name}`;
        inspectSelect.appendChild(opt);
    });

    const tbody = document.getElementById("strategies-matrix-body");
    tbody.innerHTML = "";

    strats.forEach(s => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${s.id}</strong></td>
            <td>${s.name}</td>
            <td>${s.type}</td>
            <td>${s.trades}</td>
            <td>${s.wins}W / ${s.losses}L</td>
            <td>${s.win_rate_pct}%</td>
            <td>${formatINR(s.gross_pnl, true)}</td>
            <td class="color-amber">${formatINR(s.drag_inr)}</td>
            <td class="${s.net_pnl >= 0 ? 'color-pos' : 'color-neg'}"><strong>${formatINR(s.net_pnl, true)}</strong></td>
            <td>${s.profit_factor.toFixed(2)}</td>
            <td>${formatINR(s.expectancy, true)}</td>
            <td><span class="${s.trades > 0 && s.win_rate_pct >= 60 ? 'badge-pos' : 'badge-neg'}">${s.status}</span></td>
        `;
        tbody.appendChild(tr);
    });

    renderStrategyInspector(strats[0].id);
    renderPlotlyStrategyPnl();
}

function renderStrategyInspector(stratId) {
    if (!cachedStrategiesData) return;
    const s = cachedStrategiesData.strategies.find(item => item.id === stratId);
    if (!s) return;

    document.getElementById("inspect-strat-details").innerHTML = `
        <div><strong>Strategy:</strong> ${s.name} (<code>${s.id}</code>)</div>
        <div><strong>Regime Type:</strong> ${s.type}</div>
        <div><strong>Permitted Direction:</strong> ${s.direction} (Options Buying Only)</div>
        <div><strong>Execution Window:</strong> ${s.timeframe}</div>
        <div><strong>Trigger Criteria:</strong> ${s.trigger}</div>
        <div><strong>Sample Audit:</strong> ${s.trades} Trades executed | ${s.win_rate_pct}% Win Rate | Net P&L: ${formatINR(s.net_pnl, true)}</div>
    `;
}

function renderPlotlyStrategyPnl() {
    if (!cachedStrategiesData) return;
    const active = cachedStrategiesData.strategies.filter(s => s.trades > 0);
    if (active.length === 0) return;

    const ids = active.map(s => s.id);
    const pnls = active.map(s => s.net_pnl);
    const colors = pnls.map(p => p >= 0 ? "#10B981" : "#F43F5E");

    const trace = {
        x: ids,
        y: pnls,
        type: 'bar',
        marker: { color: colors },
        text: pnls.map(p => formatINR(p, true)),
        textposition: 'outside'
    };

    const layout = {
        template: 'plotly_dark',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { l: 45, r: 20, t: 25, b: 35 },
        height: 280,
        xaxis: { gridcolor: 'rgba(255,255,255,0.04)' },
        yaxis: { gridcolor: 'rgba(255,255,255,0.04)' }
    };

    Plotly.react('plotly-strategy-pnl-chart', [trace], layout, { responsive: true, displayModeBar: false });
}

// -------------------------------------------------------------
// TAB 4: EQUITY CURVE & RISK ANALYTICS
// -------------------------------------------------------------
let cachedEquityData = null;

async function fetchEquityCurve() {
    try {
        const res = await fetch(`/api/equity-curve?underlying_filter=${STATE.symbol}`);
        cachedEquityData = await res.json();
        renderPlotlyEquityCurve();
    } catch (e) {
        console.error("Equity curve fetch error:", e);
    }
}

function renderPlotlyEquityCurve() {
    if (!cachedEquityData || !cachedEquityData.points || cachedEquityData.points.length === 0) return;

    const pts = cachedEquityData.points;
    const times = pts.map(p => p.time.split("T")[0] || p.time);
    const equities = pts.map(p => p.equity);
    const drawdowns = pts.map(p => p.drawdown_pct);

    const eqTrace = {
        x: times,
        y: equities,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Portfolio Equity (INR)',
        line: { color: '#10B981', width: 2.5 },
        fill: 'tozeroy',
        fillcolor: 'rgba(16, 185, 129, 0.15)',
        xaxis: 'x',
        yaxis: 'y'
    };

    const ddTrace = {
        x: times,
        y: drawdowns,
        type: 'scatter',
        mode: 'lines',
        name: 'Drawdown %',
        line: { color: '#F43F5E', width: 1.5 },
        fill: 'tozeroy',
        fillcolor: 'rgba(244, 63, 94, 0.2)',
        xaxis: 'x',
        yaxis: 'y2'
    };

    const layout = {
        template: 'plotly_dark',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { l: 60, r: 20, t: 20, b: 35 },
        height: 440,
        showlegend: true,
        legend: { orientation: 'h', y: 1.05, x: 0 },
        xaxis: { gridcolor: 'rgba(255,255,255,0.04)' },
        yaxis: {
            domain: [0.32, 1.0],
            gridcolor: 'rgba(255,255,255,0.04)',
            title: 'Account Equity (₹)'
        },
        yaxis2: {
            domain: [0.0, 0.24],
            gridcolor: 'rgba(255,255,255,0.03)',
            title: 'Drawdown %'
        }
    };

    Plotly.react('plotly-equity-curve-chart', [eqTrace, ddTrace], layout, { responsive: true, displayModeBar: false });
}

// -------------------------------------------------------------
// ACTIONS (ORDER EXECUTION / CLOSE)
// -------------------------------------------------------------
async function executePaperOrder() {
    const sym = STATE.symbol;
    const dir = STATE.direction;
    const strike = parseFloat(document.getElementById("strike-select").value);

    try {
        const res = await fetch("/api/order/paper-buy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                underlying: sym,
                option_type: dir,
                strike: strike,
                strategy_id: "DONCHIAN"
            })
        });

        const data = await res.json();
        if (res.ok) {
            showToast(`ORDER EXECUTED: ${data.message}`, "success");
            fetchPortfolioState();
        } else {
            showToast(`ERROR: ${data.detail}`, "error");
        }
    } catch (e) {
        showToast(`Failed to execute order: ${e.message}`, "error");
    }
}

async function squareOffActivePosition() {
    try {
        const res = await fetch("/api/order/close-position", { method: "POST" });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message, "success");
            fetchPortfolioState();
            fetchTradesJournal();
            fetchStrategies();
            fetchEquityCurve();
        } else {
            showToast(data.detail, "error");
        }
    } catch (e) {
        showToast(`Square-off failed: ${e.message}`, "error");
    }
}
