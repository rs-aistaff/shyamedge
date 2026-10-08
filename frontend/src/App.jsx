import React, { useState, useEffect, useCallback } from 'react';
import TopTickerNav from './components/TopTickerNav';
import SidebarDock from './components/SidebarDock';
import KpiStrip from './components/KpiStrip';
import TradingViewChart from './components/TradingViewChart';
import ActivePositionDesk from './components/ActivePositionDesk';
import DayJournalTab from './components/DayJournalTab';
import StrategyMatrixTab from './components/StrategyMatrixTab';
import EquityCurveTab from './components/EquityCurveTab';
import RiskRulesTab from './components/RiskRulesTab';
import { BarChart2, Calendar, Target, TrendingUp, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('chart');
  const [symbol, setSymbol] = useState('NIFTY50');
  const [timeframe, setTimeframe] = useState('5m');
  const [marketStatus, setMarketStatus] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [journalData, setJournalData] = useState(null);
  const [strategiesData, setStrategiesData] = useState(null);
  const [equityData, setEquityData] = useState(null);

  const [journalFilter, setJournalFilter] = useState('today');
  const [selectedDate, setSelectedDate] = useState(null);

  const [isExecuting, setIsExecuting] = useState(false);
  const [isSquaringOff, setIsSquaringOff] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [toasts, setToasts] = useState([]);

  const lotSizes = { NIFTY50: 65, SENSEX: 20 };

  const showToast = (message, type = 'normal') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  // 1. Fetch Market Status
  const fetchMarketStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/market-status');
      if (res.ok) setMarketStatus(await res.json());
    } catch (e) {
      console.error('Failed to fetch market status:', e);
    }
  }, []);

  // 2. Fetch Portfolio State
  const fetchPortfolio = useCallback(async () => {
    try {
      const res = await fetch(`/api/portfolio-state?underlying_filter=${symbol}`);
      if (res.ok) setPortfolio(await res.json());
    } catch (e) {
      console.error('Failed to fetch portfolio state:', e);
    }
  }, [symbol]);

  // 3. Fetch Chart Data
  const fetchChart = useCallback(async () => {
    try {
      const res = await fetch(`/api/chart-data?symbol=${symbol}&days=3`);
      if (res.ok) setChartData(await res.json());
    } catch (e) {
      console.error('Failed to fetch chart data:', e);
    }
  }, [symbol]);

  // 4. Fetch Trades Journal
  const fetchJournal = useCallback(async () => {
    try {
      const res = await fetch(`/api/trades?date_filter=${journalFilter}&underlying_filter=${symbol}`);
      if (res.ok) {
        const data = await res.json();
        setJournalData(data);
        if (!selectedDate && data.selected_date) {
          setSelectedDate(data.selected_date);
        }
      }
    } catch (e) {
      console.error('Failed to fetch trades journal:', e);
    }
  }, [journalFilter, symbol, selectedDate]);

  // 5. Fetch Strategies Matrix
  const fetchStrategies = useCallback(async () => {
    try {
      const res = await fetch(`/api/strategies?underlying_filter=${symbol}`);
      if (res.ok) setStrategiesData(await res.json());
    } catch (e) {
      console.error('Failed to fetch strategies:', e);
    }
  }, [symbol]);

  // 6. Fetch Equity Curve
  const fetchEquity = useCallback(async () => {
    try {
      const res = await fetch(`/api/equity-curve?underlying_filter=${symbol}`);
      if (res.ok) setEquityData(await res.json());
    } catch (e) {
      console.error('Failed to fetch equity curve:', e);
    }
  }, [symbol]);

  // Initial Load & Lifecycle
  useEffect(() => {
    fetchMarketStatus();
    fetchPortfolio();
    fetchChart();
    fetchJournal();
    fetchStrategies();
    fetchEquity();

    // Fast Polling
    const statusTimer = setInterval(fetchMarketStatus, 1000);
    const portTimer = setInterval(fetchPortfolio, 2000);

    return () => {
      clearInterval(statusTimer);
      clearInterval(portTimer);
    };
  }, [fetchMarketStatus, fetchPortfolio, fetchChart, fetchJournal, fetchStrategies, fetchEquity]);

  // Manual Refresh
  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([
      fetchMarketStatus(),
      fetchPortfolio(),
      fetchChart(),
      fetchJournal(),
      fetchStrategies(),
      fetchEquity(),
    ]);
    setIsRefreshing(false);
    showToast('Market tape & portfolio data refreshed.', 'normal');
  };

  // Order Execution
  const handleExecuteOrder = async (orderPayload) => {
    setIsExecuting(true);
    try {
      const res = await fetch('/api/order/paper-buy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderPayload),
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message, 'success');
        fetchPortfolio();
      } else {
        showToast(data.detail || 'Execution rejected.', 'error');
      }
    } catch (e) {
      showToast(`Order failed: ${e.message}`, 'error');
    } finally {
      setIsExecuting(false);
    }
  };

  // Square Off
  const handleSquareOff = async () => {
    setIsSquaringOff(true);
    try {
      const res = await fetch('/api/order/close-position', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message, 'success');
        fetchPortfolio();
        fetchJournal();
        fetchStrategies();
        fetchEquity();
      } else {
        showToast(data.detail || 'Square-off failed.', 'error');
      }
    } catch (e) {
      showToast(`Square-off failed: ${e.message}`, 'error');
    } finally {
      setIsSquaringOff(false);
    }
  };

  // DB Controls
  const handleClearPosition = async () => {
    try {
      const res = await fetch('/api/db/clear-position', { method: 'POST' });
      const data = await res.json();
      showToast(data.message, 'success');
      fetchPortfolio();
    } catch (e) {
      showToast(`Clear failed: ${e.message}`, 'error');
    }
  };

  const handleSyncBenchmark = async () => {
    showToast('Syncing 73 verified benchmark trades...', 'normal');
    try {
      const res = await fetch('/api/db/sync-benchmark', { method: 'POST' });
      const data = await res.json();
      showToast(data.message, 'success');
      fetchPortfolio();
      fetchJournal();
      fetchStrategies();
      fetchEquity();
    } catch (e) {
      showToast(`Sync failed: ${e.message}`, 'error');
    }
  };

  const handleFactoryReset = async () => {
    if (window.confirm('FACTORY RESET: Wipe all orders, positions, signals, and trades to 0?')) {
      try {
        const res = await fetch('/api/db/factory-reset', { method: 'POST' });
        const data = await res.json();
        showToast(data.message, 'error');
        fetchPortfolio();
        fetchJournal();
        fetchStrategies();
        fetchEquity();
      } catch (e) {
        showToast(`Reset failed: ${e.message}`, 'error');
      }
    }
  };

  const handleEmergencyKill = () => {
    if (window.confirm('EMERGENCY KILL SWITCH: Liquidate all active positions and disarm algorithms?')) {
      handleSquareOff();
      showToast('🛑 EMERGENCY KILL SWITCH TRIGGERED: Liquidated to cash.', 'error');
    }
  };

  return (
    <div className="terminal-app-container">
      {/* 1. Top Institutional Ticker Bar */}
      <TopTickerNav
        marketStatus={marketStatus}
        symbol={symbol}
        onSelectSymbol={setSymbol}
        onRefresh={handleManualRefresh}
        isRefreshing={isRefreshing}
      />

      <div className="workspace-layout">
        {/* 2. Left Execution & Controls Dock */}
        <SidebarDock
          symbol={symbol}
          onSelectSymbol={setSymbol}
          lotSizes={lotSizes}
          onClearPosition={handleClearPosition}
          onSyncBenchmark={handleSyncBenchmark}
          onFactoryReset={handleFactoryReset}
          onEmergencyKill={handleEmergencyKill}
        />

        {/* 3. Main Stage */}
        <main className="main-stage">
          <div className="stage-header">
            <div>
              <h1 className="stage-title">QUANTITATIVE TRADING TERMINAL</h1>
              <p className="stage-subtitle">
                Institutional algorithmic options trading desk • Real Yahoo Finance market feed • 1-Lot strict risk governance.
              </p>
            </div>
            <div className="active-contract-head-badge font-mono">
              <span className="pulse-indicator"></span>
              <span>ACTIVE: {symbol === 'NIFTY50' ? 'NIFTY 50 (LOT: 65)' : 'SENSEX (LOT: 20)'}</span>
            </div>
          </div>

          {/* Top KPI Strip */}
          <KpiStrip portfolio={portfolio} />

          {/* Navigation Tab Bar */}
          <nav className="tab-navigation font-mono">
            <button
              className={`tab-btn ${activeTab === 'chart' ? 'active' : ''}`}
              onClick={() => setActiveTab('chart')}
            >
              <BarChart2 size={14} /> <span>LIVE CHART &amp; ACTIVE POSITION</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'journal' ? 'active' : ''}`}
              onClick={() => setActiveTab('journal')}
            >
              <Calendar size={14} /> <span>DAY-BY-DAY TRADE JOURNAL</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'matrix' ? 'active' : ''}`}
              onClick={() => setActiveTab('matrix')}
            >
              <Target size={14} /> <span>15 STRATEGIES ALPHA MATRIX</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'equity' ? 'active' : ''}`}
              onClick={() => setActiveTab('equity')}
            >
              <TrendingUp size={14} /> <span>EQUITY CURVE &amp; RISK</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'rules' ? 'active' : ''}`}
              onClick={() => setActiveTab('rules')}
            >
              <ShieldCheck size={14} /> <span>RISK RULES &amp; SEBI TAXES</span>
            </button>
          </nav>

          {/* Tab Views */}
          <div className="tab-content-area">
            {activeTab === 'chart' && (
              <div className="chart-position-grid">
                <TradingViewChart
                  symbol={symbol}
                  chartData={chartData}
                  timeframe={timeframe}
                  onSelectTimeframe={setTimeframe}
                />
                <ActivePositionDesk
                  position={portfolio?.open_position}
                  symbol={symbol}
                  lotSizes={lotSizes}
                  onSquareOff={handleSquareOff}
                  isSquaringOff={isSquaringOff}
                />
              </div>
            )}

            {activeTab === 'journal' && (
              <DayJournalTab
                journalData={journalData}
                activeFilter={journalFilter}
                onSelectFilter={(f) => setJournalFilter(f)}
                selectedDate={selectedDate}
                onSelectDate={(d) => {
                  setSelectedDate(d);
                  setJournalFilter(d);
                }}
              />
            )}

            {activeTab === 'matrix' && (
              <StrategyMatrixTab strategiesData={strategiesData} />
            )}

            {activeTab === 'equity' && (
              <EquityCurveTab equityData={equityData} portfolio={portfolio} />
            )}

            {activeTab === 'rules' && <RiskRulesTab />}
          </div>
        </main>
      </div>

      {/* Floating Notifications */}
      <div className="toast-container font-mono">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            {t.type === 'success' ? (
              <CheckCircle2 size={16} className="color-emerald" />
            ) : t.type === 'error' ? (
              <AlertCircle size={16} className="color-rose" />
            ) : (
              <CheckCircle2 size={16} className="color-blue" />
            )}
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
