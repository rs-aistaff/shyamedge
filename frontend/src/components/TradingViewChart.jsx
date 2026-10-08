import React, { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries, LineSeries, HistogramSeries } from 'lightweight-charts';
import { BarChart3 } from 'lucide-react';

export default function TradingViewChart({ symbol, chartData, timeframe, onSelectTimeframe }) {
  const chartContainerRef = useRef(null);
  const chartInstanceRef = useRef(null);
  const [chartError, setChartError] = useState(null);

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
        height: 480,
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
        crosshair: {
          mode: 1,
          vertLine: {
            color: 'rgba(56, 189, 248, 0.4)',
            width: 1,
            style: 3,
          },
          horzLine: {
            color: 'rgba(56, 189, 248, 0.4)',
            width: 1,
            style: 3,
          },
        },
        rightPriceScale: {
          borderColor: 'rgba(255, 255, 255, 0.08)',
          scaleMargins: {
            top: 0.1,
            bottom: 0.25,
          },
        },
        timeScale: {
          borderColor: 'rgba(255, 255, 255, 0.08)',
          timeVisible: true,
          secondsVisible: false,
        },
      });

      chartInstanceRef.current = chart;

      // Safe series adder supporting both v4 and v5
      const addSeriesSafe = (SeriesClass, methodName, options) => {
        if (typeof chart.addSeries === 'function' && SeriesClass) {
          return chart.addSeries(SeriesClass, options);
        } else if (typeof chart[methodName] === 'function') {
          return chart[methodName](options);
        }
        return null;
      };

      const volumeSeries = addSeriesSafe(HistogramSeries, 'addHistogramSeries', {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      });

      if (chart.priceScale('volume')) {
        chart.priceScale('volume').applyOptions({
          scaleMargins: {
            top: 0.82,
            bottom: 0,
          },
          visible: false,
        });
      }

      const candleSeries = addSeriesSafe(CandlestickSeries, 'addCandlestickSeries', {
        upColor: '#10B981',
        downColor: '#F43F5E',
        borderVisible: false,
        wickUpColor: '#10B981',
        wickDownColor: '#F43F5E',
      });

      const vwapSeries = addSeriesSafe(LineSeries, 'addLineSeries', {
        color: '#06B6D4',
        lineWidth: 2,
        title: 'VWAP',
      });

      const ema20Series = addSeriesSafe(LineSeries, 'addLineSeries', {
        color: '#F59E0B',
        lineWidth: 1.5,
        title: '20 EMA',
      });

      const ema50Series = addSeriesSafe(LineSeries, 'addLineSeries', {
        color: '#A855F7',
        lineWidth: 1.5,
        title: '50 EMA',
      });

      // Populate Data
      if (chartData && chartData.candles && chartData.candles.length > 0) {
        const parsedCandles = [];
        const parsedVwap = [];
        const parsedEma20 = [];
        const parsedEma50 = [];
        const parsedVol = [];

        const seenTimes = new Set();

        chartData.candles.forEach((c, idx) => {
          let unixTime;
          if (typeof c.time === 'number') {
            unixTime = c.time > 1e11 ? Math.floor(c.time / 1000) : Math.floor(c.time);
          } else if (typeof c.time === 'string') {
            unixTime = Math.floor(new Date(c.time).getTime() / 1000);
          } else {
            unixTime = Math.floor(Date.now() / 1000) - (chartData.candles.length - idx) * 300;
          }

          if (!isNaN(unixTime) && !seenTimes.has(unixTime)) {
            seenTimes.add(unixTime);

            parsedCandles.push({
              time: unixTime,
              open: c.open,
              high: c.high,
              low: c.low,
              close: c.close,
            });

            if (chartData.vwap && chartData.vwap[idx]) {
              parsedVwap.push({ time: unixTime, value: chartData.vwap[idx].val });
            }
            if (chartData.ema20 && chartData.ema20[idx]) {
              parsedEma20.push({ time: unixTime, value: chartData.ema20[idx].val });
            }
            if (chartData.ema50 && chartData.ema50[idx]) {
              parsedEma50.push({ time: unixTime, value: chartData.ema50[idx].val });
            }
            if (chartData.volume && chartData.volume[idx]) {
              parsedVol.push({
                time: unixTime,
                value: chartData.volume[idx].volume,
                color: chartData.volume[idx].is_up ? 'rgba(16, 185, 129, 0.45)' : 'rgba(244, 63, 94, 0.45)',
              });
            }
          }
        });

        parsedCandles.sort((a, b) => a.time - b.time);
        parsedVwap.sort((a, b) => a.time - b.time);
        parsedEma20.sort((a, b) => a.time - b.time);
        parsedEma50.sort((a, b) => a.time - b.time);
        parsedVol.sort((a, b) => a.time - b.time);

        if (candleSeries) candleSeries.setData(parsedCandles);
        if (vwapSeries) vwapSeries.setData(parsedVwap);
        if (ema20Series) ema20Series.setData(parsedEma20);
        if (ema50Series) ema50Series.setData(parsedEma50);
        if (volumeSeries) volumeSeries.setData(parsedVol);

        chart.timeScale().fitContent();
      }

      setChartError(null);
    } catch (err) {
      console.error('TradingViewChart init error:', err);
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
  }, [chartData]);

  const lot = chartData?.lot_size || (symbol === 'NIFTY50' ? 65 : 20);
  const curP = chartData?.current_price;
  const netChg = chartData?.net_change;
  const pctChg = chartData?.pct_change;

  return (
    <div className="chart-container-card">
      <div className="card-toolbar">
        <div className="toolbar-left">
          <div className="chart-title-tag font-mono">
            <BarChart3 size={15} className="color-blue" />
            <span className="chart-sym-name">{symbol === 'NIFTY50' ? 'NIFTY 50' : 'SENSEX'}</span>
            <span className="chart-lot-badge">LOT: {lot}</span>
            {curP && (
              <span className="chart-spot-val font-mono">
                ₹{curP.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                <span className={`chart-delta ${netChg >= 0 ? 'color-pos' : 'color-neg'}`}>
                  {netChg >= 0 ? '+' : ''}{netChg} ({pctChg >= 0 ? '+' : ''}{pctChg}%)
                </span>
              </span>
            )}
            <span className="internet-live-pill font-mono">
              <span className="radar-dot"></span>
              REAL YAHOO FINANCE FEED
            </span>
          </div>

          <div className="timeframe-pills">
            {['1m', '3m', '5m', '15m'].map((tf) => (
              <button
                key={tf}
                className={`tf-btn ${timeframe === tf ? 'active' : ''}`}
                onClick={() => onSelectTimeframe(tf)}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        <div className="toolbar-legend font-mono">
          <span className="leg-item leg-vwap">● VWAP (Intraday)</span>
          <span className="leg-item leg-ema20">● 20 EMA</span>
          <span className="leg-item leg-ema50">● 50 EMA</span>
        </div>
      </div>

      {chartError ? (
        <div className="chart-fallback font-mono" style={{ padding: 40, textAlign: 'center', color: '#94A3B8' }}>
          <div>⚠️ Canvas initialization note: {chartError}</div>
          <div style={{ marginTop: 8, fontSize: 12 }}>Loading realtime tick stream...</div>
        </div>
      ) : (
        <div ref={chartContainerRef} className="tradingview-canvas-wrapper" />
      )}
    </div>
  );
}
