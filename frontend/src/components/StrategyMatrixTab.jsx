import React, { useState } from 'react';
import { Target, Award, Search, Info } from 'lucide-react';

export default function StrategyMatrixTab({ strategiesData }) {
  const list = strategiesData?.strategies || [];
  const [selectedStratId, setSelectedStratId] = useState(list[0]?.id || 'DONCHIAN');

  const selectedStrat = list.find((s) => s.id === selectedStratId) || list[0] || {};

  const formatINR = (val, sign = false) => {
    const num = Number(val || 0);
    const s = sign && num > 0 ? '+' : '';
    return `${s}₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="strategy-matrix-pane">
      <div className="stage-section-head">
        <div className="section-title-group">
          <Target size={18} className="color-cyan" />
          <h3>15 QUANTITATIVE STRATEGIES ALPHA MATRIX</h3>
        </div>
        <p>
          Side-by-side performance audit calibrated with SEBI statutory deductions and realistic 0.4% market slippage.
        </p>
      </div>

      {/* Strategies Table */}
      <div className="table-card">
        <div className="table-responsive">
          <table className="styled-table font-mono">
            <thead>
              <tr>
                <th>Strategy ID</th>
                <th>Strategy Name</th>
                <th>Regime Type</th>
                <th>Trades</th>
                <th>W / L</th>
                <th>Win Rate</th>
                <th>Gross P&amp;L</th>
                <th>Taxes &amp; Slip</th>
                <th>Net P&amp;L</th>
                <th>Profit Factor</th>
                <th>Expectancy</th>
                <th>Alpha Status</th>
              </tr>
            </thead>
            <tbody>
              {list.map((s) => (
                <tr
                  key={s.id}
                  className={`cursor-pointer ${selectedStratId === s.id ? 'row-selected' : ''}`}
                  onClick={() => setSelectedStratId(s.id)}
                >
                  <td><strong>{s.id}</strong></td>
                  <td>{s.name}</td>
                  <td>{s.type}</td>
                  <td>{s.trades}</td>
                  <td>{s.wins}W / {s.losses}L</td>
                  <td>
                    <span className={s.win_rate_pct >= 60 ? 'color-pos font-bold' : ''}>
                      {s.win_rate_pct.toFixed(1)}%
                    </span>
                  </td>
                  <td>{formatINR(s.gross_pnl, true)}</td>
                  <td className="color-amber">{formatINR(s.drag_inr)}</td>
                  <td className={s.net_pnl >= 0 ? 'color-pos font-bold' : 'color-neg font-bold'}>
                    {formatINR(s.net_pnl, true)}
                  </td>
                  <td>{s.profit_factor.toFixed(2)}</td>
                  <td>{formatINR(s.expectancy, true)}</td>
                  <td>
                    <span className={s.trades > 0 && s.win_rate_pct >= 60 ? 'badge-pos' : 'badge-neutral'}>
                      {s.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Matrix Bottom Grid: Attribution Chart & Inspector */}
      <div className="matrix-bottom-grid">
        <div className="m-chart-card">
          <h4>NET P&amp;L ATTRIBUTION BY STRATEGY</h4>
          <div className="strat-bars-container font-mono">
            {list.filter(s => s.trades > 0).map((s) => {
              const maxPnl = Math.max(...list.map(item => Math.abs(item.net_pnl)), 1000);
              const pct = Math.min(100, Math.max(8, (Math.abs(s.net_pnl) / maxPnl) * 100));
              return (
                <div key={s.id} className="strat-bar-row">
                  <span className="sbar-label">{s.id}</span>
                  <div className="sbar-track">
                    <div
                      className={`sbar-fill ${s.net_pnl >= 0 ? 'bg-pos' : 'bg-neg'}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className={`sbar-val ${s.net_pnl >= 0 ? 'color-pos' : 'color-neg'}`}>
                    {formatINR(s.net_pnl, true)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="m-rulebook-card">
          <div className="card-header-icon">
            <Info size={16} className="color-blue" />
            <h4>STRATEGY RULEBOOK &amp; SETUP INSPECTOR</h4>
          </div>
          <div className="input-group">
            <label htmlFor="inspect-select">Select Strategy:</label>
            <select
              id="inspect-select"
              className="styled-select font-mono"
              value={selectedStratId}
              onChange={(e) => setSelectedStratId(e.target.value)}
            >
              {list.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.id} - {s.name}
                </option>
              ))}
            </select>
          </div>

          <div className="rulebook-details font-mono">
            <div><strong>Strategy:</strong> {selectedStrat.name} (<code>{selectedStrat.id}</code>)</div>
            <div><strong>Regime Type:</strong> {selectedStrat.type}</div>
            <div><strong>Direction:</strong> {selectedStrat.direction} (Strict Options Buying Only)</div>
            <div><strong>Execution Window:</strong> {selectedStrat.timeframe}</div>
            <div><strong>Trigger Criteria:</strong> {selectedStrat.trigger}</div>
            <div>
              <strong>Sample Audit:</strong> {selectedStrat.trades} Executed | {selectedStrat.win_rate_pct}% Win Rate | Net: {formatINR(selectedStrat.net_pnl, true)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
