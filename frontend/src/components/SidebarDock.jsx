import React from 'react';
import { ShieldCheck, AlertOctagon, Trash2, RotateCcw, Activity, Layers, CheckCircle2, TrendingUp } from 'lucide-react';

export default function SidebarDock({
  symbol,
  onSelectSymbol,
  lotSizes,
  onClearPosition,
  onSyncBenchmark,
  onFactoryReset,
  onEmergencyKill
}) {
  const lot = lotSizes[symbol] || (symbol === 'NIFTY50' ? 65 : 20);

  return (
    <aside className="sidebar-dock">
      <div className="dock-header">
        <div className="dock-title-group">
          <Layers size={14} className="color-blue" />
          <h3>DESK CONTROLS</h3>
        </div>
        <span className="latency-badge font-mono">⚡ AUTONOMOUS DESK</span>
      </div>

      {/* 1. INSTANT INDEX TOGGLE: NIFTY 50 (Lot: 65) vs SENSEX (Lot: 20) */}
      <div className="dock-section">
        <label className="dock-label">INSTANT CONTRACT SWITCH</label>
        <div className="segmented-control">
          <button
            className={`seg-btn ${symbol === 'NIFTY50' ? 'active' : ''}`}
            onClick={() => onSelectSymbol('NIFTY50')}
            id="toggle-nifty50"
          >
            <span className="seg-title">NIFTY 50</span>
            <span className="seg-sub font-mono">Lot: 65 Qty</span>
          </button>
          <button
            className={`seg-btn ${symbol === 'SENSEX' ? 'active' : ''}`}
            onClick={() => onSelectSymbol('SENSEX')}
            id="toggle-sensex"
          >
            <span className="seg-title">SENSEX</span>
            <span className="seg-sub font-mono">Lot: 20 Qty</span>
          </button>
        </div>
      </div>

      {/* 2. AUTONOMOUS QUANT ENGINE STATUS */}
      <div className="dock-section autopilot-status-card">
        <div className="autopilot-head">
          <div className="status-indicator-box">
            <span className="radar-dot"></span>
            <span className="autopilot-title">QUANT ALGO AUTOPILOT</span>
          </div>
          <span className="autopilot-tag font-mono">100% AUTO</span>
        </div>
        <p className="autopilot-desc">
          Automated algorithmic execution armed. System reads 5m Yahoo Finance market candles, detects institutional breakout setups, ratchets trailing stops, and exits automatically.
        </p>
        <div className="active-contract-banner font-mono">
          <span className="ac-label">ACTIVE MONITOR:</span>
          <span className="ac-val color-blue">
            {symbol === 'NIFTY50' ? 'NIFTY 50 (1 Lot: 65 Qty)' : 'SENSEX (1 Lot: 20 Qty)'}
          </span>
        </div>
      </div>

      {/* 3. ACTIVE QUANT ALGO STRATEGIES */}
      <div className="dock-section algo-roster-card">
        <div className="roster-head">
          <Activity size={13} className="color-emerald" />
          <span className="roster-title">RUNNING ALPHA STRATEGIES</span>
        </div>
        <div className="roster-list font-mono">
          <div className="roster-item">
            <CheckCircle2 size={12} className="color-emerald" />
            <span>15m Opening Range Breakout</span>
          </div>
          <div className="roster-item">
            <CheckCircle2 size={12} className="color-emerald" />
            <span>VWAP + 20/50 EMA Trend</span>
          </div>
          <div className="roster-item">
            <CheckCircle2 size={12} className="color-emerald" />
            <span>Donchian 20-Period Breakout</span>
          </div>
          <div className="roster-item">
            <CheckCircle2 size={12} className="color-emerald" />
            <span>Central Pivot Range (CPR) Push</span>
          </div>
        </div>
      </div>

      {/* 4. INSTITUTIONAL RISK GOVERNANCE BOUNDS */}
      <div className="dock-section risk-card">
        <div className="risk-head">
          <div className="risk-title-box">
            <ShieldCheck size={14} className="color-amber" />
            <span className="risk-title">INSTITUTIONAL RISK BOUNDS</span>
          </div>
          <span className="risk-status">STRICT</span>
        </div>
        <div className="risk-grid font-mono">
          <div className="risk-metric">
            <span className="r-label">Capital Base</span>
            <span className="r-val">₹30,000</span>
          </div>
          <div className="risk-metric">
            <span className="r-label">Position Sizing</span>
            <span className="r-val color-blue">1 Lot ({lot} Qty)</span>
          </div>
          <div className="risk-metric">
            <span className="r-label">Max Risk/Trade</span>
            <span className="r-val color-amber">₹900 (3%)</span>
          </div>
          <div className="risk-metric">
            <span className="r-label">Daily Stop Cap</span>
            <span className="r-val color-neg">₹1,200 (4%)</span>
          </div>
          <div className="risk-metric">
            <span className="r-label">Profit Ratchet</span>
            <span className="r-val color-pos">+8%, +16%, +24%</span>
          </div>
          <div className="risk-metric">
            <span className="r-label">Order Type</span>
            <span className="r-val">Strict Buy Only</span>
          </div>
        </div>
      </div>

      {/* 5. EMERGENCY KILL SWITCH */}
      <div className="dock-section">
        <button className="btn-kill-switch" onClick={onEmergencyKill} id="btn-emergency-kill">
          <AlertOctagon size={14} /> EMERGENCY KILL SWITCH
        </button>
      </div>

      {/* 6. DATABASE MAINTENANCE */}
      <div className="dock-section db-card">
        <div className="db-head">
          <span>🧹 DATABASE MAINTENANCE</span>
        </div>
        <div className="db-actions">
          <button className="btn-db" onClick={onClearPosition} title="Close open position immediately" id="btn-go-flat">
            <span>🧹 Go Flat</span>
          </button>
          <button className="btn-db" onClick={onSyncBenchmark} title="Sync 73 verified benchmark trades" id="btn-sync-bench">
            <RotateCcw size={11} /> <span>Sync Bench</span>
          </button>
          <button className="btn-db btn-db-danger" onClick={onFactoryReset} title="Wipe database completely" id="btn-zero-out">
            <Trash2 size={11} /> <span>Zero Out</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
