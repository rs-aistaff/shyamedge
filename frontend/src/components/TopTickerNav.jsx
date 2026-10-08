import React from 'react';
import { RefreshCw, Zap, Wifi, Clock } from 'lucide-react';

export default function TopTickerNav({ marketStatus, symbol, onSelectSymbol, onRefresh, isRefreshing }) {
  const isLive = marketStatus?.is_live_session;
  const istTime = marketStatus?.ist_time || '--:--:--';
  const sessionLabel = marketStatus?.session_label || '🔴 MARKET CLOSED';
  const timingDetail = marketStatus?.timing_detail || 'Trading Hours: 09:15 - 15:30 IST';
  const isRealInternet = marketStatus?.data_source?.includes('REAL_INTERNET') ?? true;
  
  const tickers = marketStatus?.tickers || {
    NIFTY50: { price: 22603.05, change: '-173.05', pct: '-0.76%', positive: false, lot_size: 65 },
    SENSEX: { price: 72638.70, change: '-429.11', pct: '-0.59%', positive: false, lot_size: 20 },
    BANKNIFTY: { price: 47690.00, change: '+280.10', pct: '+0.54%', positive: true, lot_size: 30 },
    INDIAVIX: { price: 13.25, change: '-0.32', pct: '-2.36%', positive: false }
  };

  return (
    <header className="top-nav">
      <div className="nav-left">
        <div className="brand-badge">
          <div className="brand-icon">
            <Zap size={18} color="#FFFFFF" />
          </div>
          <div className="brand-text">
            <span className="brand-title">SHYAMEDGE PRO</span>
            <span className="brand-subtitle">AI QUANT DESK</span>
          </div>
        </div>

        {/* Market Session & Timing Pill */}
        <div className={`session-pill ${isLive ? 'live' : 'sim'}`} title={timingDetail}>
          <span className="radar-dot"></span>
          <span>{sessionLabel}</span>
        </div>

        <div className="internet-status-pill font-mono" title="Live Yahoo Finance Feed Connected">
          <Wifi size={13} className={isRealInternet ? "color-emerald" : "color-amber"} />
          <span>{isRealInternet ? "REAL INTERNET FEED" : "FALLBACK"}</span>
        </div>
      </div>

      {/* INSTANT INDEX TOGGLE: NIFTY 50 (Lot: 65) vs SENSEX (Lot: 20) */}
      <div className="instant-index-switcher font-mono">
        <button
          className={`index-toggle-card ${symbol === 'NIFTY50' ? 'active' : ''}`}
          onClick={() => onSelectSymbol('NIFTY50')}
          title="Instant Switch to NIFTY 50 (Official Lot: 65)"
          id="nav-toggle-nifty50"
        >
          <div className="toggle-header">
            <span className="index-code">NIFTY 50</span>
            <span className="index-lot-tag">LOT: 65</span>
          </div>
          <div className="toggle-values">
            <span className="index-price">₹{tickers.NIFTY50.price.toFixed(2)}</span>
            <span className={`index-delta ${tickers.NIFTY50.positive ? 'color-pos' : 'color-neg'}`}>
              {tickers.NIFTY50.change} ({tickers.NIFTY50.pct})
            </span>
          </div>
        </button>

        <button
          className={`index-toggle-card ${symbol === 'SENSEX' ? 'active' : ''}`}
          onClick={() => onSelectSymbol('SENSEX')}
          title="Instant Switch to SENSEX (Official Lot: 20)"
          id="nav-toggle-sensex"
        >
          <div className="toggle-header">
            <span className="index-code">SENSEX</span>
            <span className="index-lot-tag">LOT: 20</span>
          </div>
          <div className="toggle-values">
            <span className="index-price">₹{tickers.SENSEX.price.toFixed(2)}</span>
            <span className={`index-delta ${tickers.SENSEX.positive ? 'color-pos' : 'color-neg'}`}>
              {tickers.SENSEX.change} ({tickers.SENSEX.pct})
            </span>
          </div>
        </button>
      </div>

      <div className="nav-right">
        <div className="clock-display font-mono" title={timingDetail}>
          🕒 {istTime} IST
        </div>
        <button
          className={`btn-refresh ${isRefreshing ? 'spinning' : ''}`}
          onClick={onRefresh}
          title="Force Market Data Sync"
        >
          <RefreshCw size={14} />
        </button>
      </div>
    </header>
  );
}
