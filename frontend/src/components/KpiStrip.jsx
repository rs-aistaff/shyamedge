import React from 'react';
import { DollarSign, Award, Activity, TrendingUp, ShieldAlert } from 'lucide-react';

export default function KpiStrip({ portfolio }) {
  const p = portfolio || {};
  const equity = p.account_equity || 30000;
  const netPnl = p.realized_net_pnl || 0;
  const mtm = p.unrealized_mtm || 0;
  const winRate = p.win_rate_pct || 0;
  const pf = p.profit_factor || 0;
  const maxDd = p.max_drawdown_pct || 0;
  const retCap = p.return_on_capital_pct || 0;
  const hasPos = p.has_open_position;

  const formatINR = (val, sign = false) => {
    const num = Number(val || 0);
    const s = sign && num > 0 ? '+' : '';
    return `${s}₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <section className="kpi-strip" aria-label="Executive Performance KPIs">
      {/* 1. Account Equity */}
      <div className="kpi-card">
        <div className="kpi-head">
          <span className="kpi-label">ACCOUNT EQUITY</span>
          <DollarSign size={14} className="color-cyan" />
        </div>
        <div className="kpi-val font-mono">{formatINR(equity)}</div>
        <div className="kpi-delta font-mono badge-pos">
          +{retCap}% on Initial Capital
        </div>
      </div>

      {/* 2. Realized Net P&L */}
      <div className="kpi-card">
        <div className="kpi-head">
          <span className="kpi-label">REALIZED NET P&L</span>
          <Award size={14} className="color-emerald" />
        </div>
        <div className={`kpi-val font-mono ${netPnl >= 0 ? 'color-pos' : 'color-neg'}`}>
          {formatINR(netPnl, true)}
        </div>
        <div className="kpi-delta font-mono badge-pos">
          {winRate}% Win Rate ({p.winning_trades || 0}W / {p.losing_trades || 0}L)
        </div>
      </div>

      {/* 3. Running Unrealized MTM */}
      <div className="kpi-card">
        <div className="kpi-head">
          <span className="kpi-label">RUNNING UNREALIZED MTM</span>
          <Activity size={14} className={hasPos ? 'color-emerald' : 'text-muted'} />
        </div>
        <div className={`kpi-val font-mono ${hasPos ? (mtm >= 0 ? 'color-pos' : 'color-neg') : ''}`}>
          {hasPos ? formatINR(mtm, true) : '₹0.00'}
        </div>
        <div className="kpi-delta font-mono">
          {hasPos ? (
            <span className={mtm >= 0 ? 'badge-pos' : 'badge-neg'}>
              ACTIVE POSITION
            </span>
          ) : (
            <span className="badge-neutral">FLAT CASH</span>
          )}
        </div>
      </div>

      {/* 4. Profit Factor */}
      <div className="kpi-card">
        <div className="kpi-head">
          <span className="kpi-label">PROFIT FACTOR</span>
          <TrendingUp size={14} className="color-blue" />
        </div>
        <div className="kpi-val font-mono color-pos">
          {pf.toFixed(2)}
        </div>
        <div className="kpi-delta font-mono badge-pos">
          Benchmark &gt; 2.0 (Institutional)
        </div>
      </div>

      {/* 5. Max Drawdown */}
      <div className="kpi-card">
        <div className="kpi-head">
          <span className="kpi-label">MAX DRAWDOWN</span>
          <ShieldAlert size={14} className="color-amber" />
        </div>
        <div className="kpi-val font-mono color-amber">
          {maxDd.toFixed(2)}%
        </div>
        <div className="kpi-delta font-mono badge-pos">
          &lt; 9.7% Strict Safe Boundary
        </div>
      </div>
    </section>
  );
}
