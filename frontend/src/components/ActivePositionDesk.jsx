import React from 'react';
import { ShieldCheck, Crosshair, Zap, ArrowUpRight, Flame } from 'lucide-react';

export default function ActivePositionDesk({
  position,
  symbol,
  lotSizes,
  onSquareOff,
  isSquaringOff
}) {
  const hasPos = Boolean(position);
  const lot = lotSizes ? (lotSizes[symbol] || (symbol === 'NIFTY50' ? 65 : 20)) : (symbol === 'NIFTY50' ? 65 : 20);

  const formatINR = (val, sign = false) => {
    const num = Number(val || 0);
    const s = sign && num > 0 ? '+' : '';
    return `${s}₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  if (!hasPos) {
    return (
      <div className="position-desk-card">
        <div className="pos-card-head">
          <span className="pos-title">⚡ RUNNING POSITION &amp; MTM</span>
          <span className="badge-neutral font-mono">FLAT CASH</span>
        </div>

        <div className="pos-empty-body">
          <div className="empty-shield-icon">
            <ShieldCheck size={42} className="color-emerald" />
          </div>
          <h4>AI QUANT ENGINES ARMED</h4>
          <p>
            Autonomous alpha models (ORB, VWAP Breakout, Donchian Channel, CPR) are calibrated and armed. Capital preserved at ₹30,000 cash.
          </p>

          <div className="scanner-hud-box font-mono">
            <div className="scanner-hud-row">
              <span className="hud-label">Active Index:</span>
              <span className="hud-val color-blue">{symbol === 'NIFTY50' ? 'NIFTY 50 (1 Lot: 65 Qty)' : 'SENSEX (1 Lot: 20 Qty)'}</span>
            </div>
            <div className="scanner-hud-row">
              <span className="hud-label">Live Data Stream:</span>
              <span className="hud-val color-emerald">Yahoo Finance (Real Internet Feed)</span>
            </div>
            <div className="scanner-hud-row">
              <span className="hud-label">Execution Mode:</span>
              <span className="hud-val color-purple">Strict Options Buying (CE/PE)</span>
            </div>
            <div className="scanner-hud-row">
              <span className="hud-label">Risk Governance:</span>
              <span className="hud-val">Max Loss ₹900 | Target +30% | 1 Lot Fixed</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const p = position;
  const entryP = p.entry_price || 140;
  const curP = p.current_price || entryP;
  const slP = p.stop_loss || (entryP * 0.85);
  const tgtP = p.target || (entryP * 1.30);
  const mtm = p.unrealized_pnl || 0;
  const retPct = p.return_pct || 0;
  const trailingSl = p.trailing_sl;

  // Trailing stop status label
  let trailLabel = 'Initial Stop Loss Active (-15%)';
  if (trailingSl) {
    if (trailingSl >= entryP * 1.15) {
      trailLabel = `🚀 Momentum Locked @ ₹${trailingSl.toFixed(2)} (+16%)`;
    } else if (trailingSl >= entryP * 1.05) {
      trailLabel = `⭐ Profit Locked @ ₹${trailingSl.toFixed(2)} (+8%)`;
    } else if (trailingSl >= entryP) {
      trailLabel = `🛡️ Breakeven Protected @ ₹${trailingSl.toFixed(2)} (0 Risk)`;
    }
  }

  // Progress Bar Percentage
  let pct = ((curP - slP) / (tgtP - slP)) * 100;
  pct = Math.max(5, Math.min(100, pct));

  return (
    <div className="position-desk-card">
      <div className="pos-card-head">
        <span className="pos-title">⚡ RUNNING POSITION &amp; MTM</span>
        <span className="badge-pos font-mono">ACTIVE LONG</span>
      </div>

      <div className="pos-active-body">
        {/* Contract Symbol & Lot */}
        <div className="pos-contract-row font-mono">
          <span className="pos-symbol-text">{p.option_symbol}</span>
          <span className="pos-qty-pill">{p.quantity} QTY (1 Lot)</span>
        </div>

        {/* Big MTM Block */}
        <div className="pos-mtm-block font-mono">
          <div className="mtm-label">LIVE UNREALIZED MTM</div>
          <div className={`mtm-amount ${mtm >= 0 ? 'color-pos' : 'color-neg'}`}>
            {formatINR(mtm, true)}
          </div>
          <div className={`mtm-pct ${retPct >= 0 ? 'color-pos' : 'color-neg'}`}>
            {retPct >= 0 ? '+' : ''}{retPct.toFixed(2)}% Return
          </div>
        </div>

        {/* Trailing Stop Ratchet Progress Bar */}
        <div className="trailing-progress-box">
          <div className="prog-labels font-mono">
            <span>SL: ₹{slP.toFixed(2)}</span>
            <span>CMP: ₹{curP.toFixed(2)}</span>
            <span>TGT: ₹{tgtP.toFixed(2)}</span>
          </div>
          <div className="prog-track">
            <div className="prog-fill" style={{ width: `${pct}%` }}></div>
          </div>
          <div className="trailing-status-pill font-mono">
            {trailLabel}
          </div>
        </div>

        {/* Price Grid */}
        <div className="pos-price-grid font-mono">
          <div className="price-cell">
            <span className="cell-label">Entry Price</span>
            <span className="cell-val">₹{entryP.toFixed(2)}</span>
          </div>
          <div className="price-cell">
            <span className="cell-label">Current CMP</span>
            <span className={`cell-val ${curP >= entryP ? 'color-pos' : 'color-neg'}`}>
              ₹{curP.toFixed(2)}
            </span>
          </div>
          <div className="price-cell">
            <span className="cell-label">Option Delta (Δ)</span>
            <span className="cell-val">{p.greeks?.delta || '0.52'}</span>
          </div>
          <div className="price-cell">
            <span className="cell-label">Theta Decay</span>
            <span className="cell-val color-amber">{p.greeks?.theta || '-₹18.40/d'}</span>
          </div>
        </div>

        {/* Square-off Button */}
        <button
          className="btn-square-off"
          onClick={onSquareOff}
          disabled={isSquaringOff}
        >
          {isSquaringOff ? 'TRANSMITTING SQUARE-OFF...' : '🛑 SQUARE OFF POSITION (MARKET)'}
        </button>
      </div>
    </div>
  );
}
