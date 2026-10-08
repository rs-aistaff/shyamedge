import React, { Component, StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class RootErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Root React Error Caught:", error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: 40,
          background: '#06080F',
          color: '#F8FAFC',
          fontFamily: "'JetBrains Mono', Consolas, monospace",
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            maxWidth: 800,
            background: '#0F172A',
            border: '1px solid #F43F5E',
            borderRadius: 12,
            padding: 30,
            boxShadow: '0 10px 40px rgba(0,0,0,0.8)'
          }}>
            <h2 style={{ color: '#F43F5E', marginBottom: 12 }}>⚠️ Terminal Interface Encountered an Issue</h2>
            <p style={{ color: '#94A3B8', marginBottom: 20 }}>
              The runtime caught an unhandled exception:
            </p>
            <pre style={{
              background: '#020617',
              padding: 16,
              borderRadius: 8,
              color: '#F87171',
              overflowX: 'auto',
              fontSize: 12,
              marginBottom: 20
            }}>
              {this.state.error && this.state.error.toString()}
            </pre>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: '#2563EB',
                border: 'none',
                color: '#FFF',
                padding: '10px 20px',
                borderRadius: 6,
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              🔄 Reload Desk
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RootErrorBoundary>
      <App />
    </RootErrorBoundary>
  </StrictMode>,
)
