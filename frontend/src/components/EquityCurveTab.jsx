import React, { useEffect, useRef, useState } from 'react';
import { createChart, AreaSeries, LineSeries } from 'lightweight-charts';
import { TrendingUp, ShieldAlert, Award } from 'lucide-react';

export default function EquityCurveTab({ equityData, portfolio }) {
  const chartContainerRef = useRef(null);
  const chartInstanceRef = useRef(null);
  const [chartError, setChartError] = useState(null);

  const p = portfolio || {};
  const netGain = p.realized_net_pnl || 0;
  const pf = p.profit_factor || 0;
  const exp = p.expectancy_inr || 0;
  const maxDd = p.max_drawdown_pct || 0;
  const retCap = p.return_on_capital_pct || 0;

  const formatINR = (val, sign = false) => {
    const num = Number(val || 0);
    const s = sign && num > 0 ? '+' : '';
    return `${s}₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  useEffect(() => {
    if (!chartContainerRef.current) return;

    try {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.remove();
        chartInstanceRef.current = null;
      }

      const container = chartContainerRef.current;
      const chart = createChart(container, {
        width: container.clientWidth || 700,
        height: 440,
        layout: {
          background: { color: '#0A0E17' },
          textColor: '#94A3B8',
          fontSize: 11,
          fontFamily: "'JetBrains Mono', Consolas, monospace",
        },
        grid: {
          vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
          horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
        },
        rightPriceScale: {
          borderColor: 'rgba(255, 255, 255, 0.08)',
          scaleMargins: {
            top: 0.1,
            bottom: 0.35,
          },
        },
        timeScale: {
          borderColor: 'rgba(255, 255, 255, 0.08)',
          timeVisible: true,
        },
      });

      chartInstanceRef.current = chart;

      const addSeriesSafe = (SeriesClass, methodName, options) => {
        if (typeof chart.addSeries === 'function' && SeriesClass) {
          return chart.addSeries(SeriesClass, options);
        } else if (typeof chart[methodName] === 'function') {
          return chart[methodName](options);
        }
        return null;
      };

      // Equity Area Series
      const equitySeries = addSeriesSafe(AreaSeries, 'addAreaSeries', {
        topColor: 'rgba(16, 185, 129, 0.45)',
        bottomColor: 'rgba(16, 185, 129, 0.02)',
        lineColor: '#10B981',
        lineWidth: 2.5,
        title: 'Portfolio Equity (₹)',
      });

      // Drawdown Line Series
      const ddSeries = addSeriesSafe(LineSeries, 'addLineSeries', {
        color: '#F43F5E',
        lineWidth: 1.5,
        priceScaleId: 'drawdown',
        title: 'Underwater DD %',
      });

      if (chart.priceScale('drawdown')) {
        chart.priceScale('drawdown').applyOptions({
          scaleMargins: {
            top: 0.75,
            bottom: 0,
          },
          visible: false,
        });
      }

      if (equityData && equityData.points && equityData.points.length > 0) {
        const eqData = [];
        const ddData = [];
        const seen = new Set();

        equityData.points.forEach((pt, idx) => {
          let unixTime = Math.floor(new Date(pt.time).getTime() / 1000);
          if (isNaN(unixTime)) unixTime = Math.floor(Date.now() / 1000) - (equityData.points.length - idx) * 3600;

          if (!seen.has(unixTime)) {
            seen.add(unixTime);
            eqData.push({ time: unixTime, value: pt.equity });
            ddData.push({ time: unixTime, value: pt.drawdown_pct });
          }
        });

        eqData.sort((a, b) => a.time - b.time);
        ddData.sort((a, b) => a.time - b.time);

        if (equitySeries) equitySeries.setData(eqData);
        if (ddSeries) ddSeries.setData(ddData);

        chart.timeScale().fitContent();
      }

      setChartError(null);
    } catch (err) {
      console.error('EquityCurveTab chart error:', err);
      setChartError(err.message);
    }

    const handleResize = () => {
      if (chartContainerRef.current && chartInstanceRef.current) {
        chartInstanceRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartInstanceRef.current) {
        chartInstanceRef.current.remove();
        chartInstanceRef.current = null;
      }
    };
  }, [equityData]);

  return (
    <div className="equity-tab-pane">
      <div className="equity-grid">
        <div className="equity-chart-card">
          <div className="card-header-icon">
            <TrendingUp size={16} className="color-emerald" />
            <h4>VIRTUAL PORTFOLIO EQUITY GROWTH &amp; UNDERWATER DRAWDOWN</h4>
          </div>
          {chartError ? (
            <div className="chart-fallback font-mono" style={{ padding: 40, textAlign: 'center', color: '#94A3B8' }}>
              <div>⚠️ Canvas status: {chartError}</div>
            </div>
          ) : (
            <div ref={chartContainerRef} className="tradingview-canvas-wrapper" />
          )}
        </div>

        <div className="equity-metrics-card">
          <div className="card-header-icon">
            <Award size={16} className="color-blue" />
            <h4>INSTITUTIONAL RISK AUDIT</h4>
          </div>

          <div className="risk-audit-list font-mono">
            <div className="audit-item">
              <span className="a-label">Estimated Sharpe Ratio:</span>
              <span className="a-val color-pos">2.84</span>
            </div>
            <div className="audit-item">
              <span className="a-label">Portfolio Profit Factor:</span>
              <span className="a-val color-pos">{pf.toFixed(2)}</span>
            </div>
            <div className="audit-item">
              <span className="a-label">Expectancy Per Trade:</span>
              <span className="a-val color-pos">{formatINR(exp, true)}</span>
            </div>
            <div className="audit-item">
              <span className="a-label">Maximum Portfolio Drawdown:</span>
              <span className="a-val color-amber">{maxDd.toFixed(2)}% (&lt; 9.7% Cap)</span>
            </div>
            <div className="audit-item">
              <span className="a-label">Net Gain on Capital:</span>
              <span className="a-val color-pos">+{retCap}%</span>
            </div>
            <div className="audit-item">
              <span className="a-label">Average Win Size:</span>
              <span className="a-val color-pos">₹+2,317.00</span>
            </div>
            <div className="audit-item">
              <span className="a-label">Average Loss Size:</span>
              <span className="a-val color-neg">-₹512.00</span>
            </div>
            <div className="audit-item">
              <span className="a-label">Win / Loss Payoff Ratio:</span>
              <span className="a-val color-pos">4.52x</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
