import React from 'react';
import { ShieldCheck, Info } from 'lucide-react';

export default function RiskRulesTab() {
  const charges = [
    {
      name: 'Securities Transaction Tax (STT)',
      rate: '0.10% on Sell Turnover',
      applied: 'Exact Statutory Calculation',
      impact: 'Direct Sell-side P&L Drag',
    },
    {
      name: 'Exchange Turnover Charges',
      rate: '0.03503% on NSE Option Premium',
      applied: 'Exact Exchange Rate',
      impact: 'Turnover Friction',
    },
    {
      name: 'Brokerage',
      rate: '₹20.00 / executed order (Flat ₹40 round-trip)',
      applied: 'Fixed per Order',
      impact: 'Execution Fixed Drag',
    },
    {
      name: 'GST',
      rate: '18.0% on (Brokerage + Exchange Charges)',
      applied: 'Exact Statutory Deduction',
      impact: 'Tax Deduction',
    },
    {
      name: 'SEBI Turnover Charges',
      rate: '₹10 per crore (0.0001%)',
      applied: 'Exact Regulatory Rate',
      impact: 'Turnover Drag',
    },
    {
      name: 'Stamp Duty',
      rate: '0.003% on Buy Turnover',
      applied: 'Exact Stamp Act Rate',
      impact: 'Buy-side Friction',
    },
    {
      name: 'Microstructure Slippage',
      rate: '0.40% adverse fill on entry & exit',
      applied: 'Realistic Orderbook Fill',
      impact: 'Execution Drag',
    },
  ];

  return (
    <div className="risk-rules-pane">
      <div className="stage-section-head">
        <div className="section-title-group">
          <ShieldCheck size={18} className="color-amber" />
          <h3>STATUTORY REGULATORY CHARGES &amp; SLIPPAGE ARCHITECTURE</h3>
        </div>
        <p>
          Every backtest trade and live paper execution accounts for SEBI 2025/2026 deductions down to the paisa.
        </p>
      </div>

      <div className="table-card">
        <table className="styled-table font-mono">
          <thead>
            <tr>
              <th>Charge Component</th>
              <th>Official Rate / Formula</th>
              <th>Applied in ShyamEdge</th>
              <th>Execution Impact</th>
            </tr>
          </thead>
          <tbody>
            {charges.map((c, idx) => (
              <tr key={idx}>
                <td><strong>{c.name}</strong></td>
                <td>{c.rate}</td>
                <td><span className="badge-pos">{c.applied}</span></td>
                <td><span className="badge-neutral">{c.impact}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="risk-guidance-card font-mono">
        <h4>🛡️ UNIVERSAL TRAILING STOP-LOSS RATCHET ENGINE</h4>
        <ul>
          <li><strong>Initial Stop Loss:</strong> Strict -15% on option premium from fill price.</li>
          <li><strong>Breakeven Ratchet (+8% gain):</strong> SL immediately jumps to +2.5% (guarantees risk-free trade).</li>
          <li><strong>Profit Lock (+15% gain):</strong> SL immediately ratchets to +8% locked profit.</li>
          <li><strong>Momentum Lock (+24% gain):</strong> SL immediately ratchets to +16% locked profit.</li>
          <li><strong>Auto-Exit Target (+30% gain):</strong> Immediate automated square-off with TARGET_HIT_30PCT.</li>
          <li><strong>Mandatory Intraday Square-Off:</strong> Strict 15:15 IST cutoff to eliminate overnight gap risk.</li>
        </ul>
      </div>
    </div>
  );
}
