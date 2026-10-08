import React from 'react';
import { Calendar, CheckCircle2, XCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function DayJournalTab({
  journalData,
  activeFilter,
  onSelectFilter,
  selectedDate,
  onSelectDate
}) {
  const jd = journalData || { trades: [], summary: {}, available_dates: [], daily_calendar: [] };
  const sm = jd.summary || { count: 0, wins: 0, losses: 0, win_rate_pct: 0, gross_pnl: 0, total_drag: 0, net_pnl: 0 };
  const trades = jd.trades || [];
  const calendar = jd.daily_calendar || [];

  const formatINR = (val, sign = false) => {
    const num = Number(val || 0);
    const s = sign && num > 0 ? '+' : '';
    return `${s}₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="journal-tab-pane">
      {/* 1. Filter Controls Bar */}
      <div className="journal-controls-bar">
        <div className="journal-filter-pills">
          <button
            className={`j-btn ${activeFilter === 'today' ? 'active' : ''}`}
            onClick={() => onSelectFilter('today')}
          >
            ⭐ TODAY ONLY
          </button>
          <button
            className={`j-btn ${activeFilter === 'all' ? 'active' : ''}`}
            onClick={() => onSelectFilter('all')}
          >
            📅 ALL HISTORICAL DATES
          </button>
        </div>

        <div className="journal-date-picker font-mono">
          <label htmlFor="journal-date-select">Choose Specific Session:</label>
          <select
            id="journal-date-select"
            className="styled-select"
            value={selectedDate || ''}
            onChange={(e) => onSelectDate(e.target.value)}
          >
            {jd.available_dates.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 2. Daily KPI Strip */}
      <div className="day-metrics-strip font-mono">
        <div className="day-metric-box">
          <span className="dm-label">SESSION TRADES</span>
          <span className="dm-val">
            {sm.count} ({sm.wins}W / {sm.losses}L • {sm.win_rate_pct}%)
          </span>
        </div>
        <div className="day-metric-box">
          <span className="dm-label">GROSS P&amp;L</span>
          <span className="dm-val">{formatINR(sm.gross_pnl, true)}</span>
        </div>
        <div className="day-metric-box">
          <span className="dm-label">STATUTORY TAXES &amp; SLIP</span>
          <span className="dm-val color-amber">{formatINR(sm.total_drag)}</span>
        </div>
        <div className="day-metric-box">
          <span className="dm-label">NET REALIZED P&amp;L</span>
          <span className={`dm-val ${sm.net_pnl >= 0 ? 'color-pos' : 'color-neg'}`}>
            {formatINR(sm.net_pnl, true)}
          </span>
        </div>
      </div>

      {/* 3. Executed Trades Table */}
      <div className="table-card">
        <div className="table-header-title">
          <h4>EXECUTED TRADES LOG • {jd.filter_label?.toUpperCase()} ({trades.length} TRADES)</h4>
        </div>
        <div className="table-responsive">
          <table className="styled-table font-mono">
            <thead>
              <tr>
                <th>Exit Time</th>
                <th>Strategy</th>
                <th>Underlying</th>
                <th>Contract</th>
                <th>Qty</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>Gross P&amp;L</th>
                <th>Taxes &amp; Slip</th>
                <th>Net P&amp;L</th>
                <th>Return %</th>
                <th>Exit Reason</th>
              </tr>
            </thead>
            <tbody>
              {trades.length === 0 ? (
                <tr>
                  <td colSpan={12} className="text-center empty-td">
                    No closed trades recorded for this date selection.
                  </td>
                </tr>
              ) : (
                trades.map((t, idx) => {
                  const exitTime = t.exit_time?.split('T')[1]?.substring(0, 8) || t.exit_time?.substring(11, 19) || '--';
                  return (
                    <tr key={idx}>
                      <td>{exitTime}</td>
                      <td>
                        <span className="badge-pos" style={{ background: 'rgba(37,99,235,0.15)', color: '#60A5FA' }}>
                          {t.strategy_id}
                        </span>
                      </td>
                      <td><strong>{t.underlying}</strong></td>
                      <td>{t.option_symbol}</td>
                      <td>{t.quantity}</td>
                      <td>₹{t.entry_price.toFixed(2)}</td>
                      <td>₹{t.exit_price.toFixed(2)}</td>
                      <td>{formatINR(t.gross_pnl, true)}</td>
                      <td className="color-amber">₹{(t.total_charges + t.slippage).toFixed(2)}</td>
                      <td className={t.net_pnl >= 0 ? 'color-pos font-bold' : 'color-neg font-bold'}>
                        {formatINR(t.net_pnl, true)}
                      </td>
                      <td className={t.return_pct >= 0 ? 'color-pos' : 'color-neg'}>
                        {t.return_pct >= 0 ? '+' : ''}{t.return_pct.toFixed(2)}%
                      </td>
                      <td>
                        <span className={t.net_pnl >= 0 ? 'badge-pos' : 'badge-neg'}>
                          {t.exit_reason}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Calendar Breakdown & Waterfall Grid */}
      <div className="calendar-waterfall-grid">
        <div className="waterfall-card">
          <h4>HISTORICAL DAILY REALIZED P&amp;L WATERFALL</h4>
          <div className="waterfall-bars-container font-mono">
            {calendar.map((c, i) => {
              const maxPnl = Math.max(...calendar.map(item => Math.abs(item.net_pnl)), 1000);
              const heightPct = Math.min(100, Math.max(10, (Math.abs(c.net_pnl) / maxPnl) * 100));
              return (
                <div key={i} className="wf-bar-col">
                  <span className={`wf-bar-val ${c.is_green ? 'color-pos' : 'color-neg'}`}>
                    {formatINR(c.net_pnl, true)}
                  </span>
                  <div className="wf-bar-track">
                    <div
                      className={`wf-bar-fill ${c.is_green ? 'bg-pos' : 'bg-neg'}`}
                      style={{ height: `${heightPct}%` }}
                    />
                  </div>
                  <span className="wf-bar-date">{c.date.substring(5)}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="calendar-card">
          <h4>HISTORICAL SESSION BREAKDOWN</h4>
          <div className="table-responsive">
            <table className="styled-table font-mono">
              <thead>
                <tr>
                  <th>Session Date</th>
                  <th>Trades</th>
                  <th>Win / Loss</th>
                  <th>Win Rate</th>
                  <th>Net Realized P&amp;L</th>
                </tr>
              </thead>
              <tbody>
                {calendar.map((c, idx) => (
                  <tr key={idx}>
                    <td><strong>{c.date}</strong></td>
                    <td>{c.trades}</td>
                    <td>{c.win_loss}</td>
                    <td>{c.win_rate}</td>
                    <td className={c.is_green ? 'color-pos font-bold' : 'color-neg font-bold'}>
                      {formatINR(c.net_pnl, true)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
