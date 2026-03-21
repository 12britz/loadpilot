import { useState, useEffect, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import NewTest from './pages/NewTest'
import TestResults from './pages/TestResults'

const APIContext = createContext({
  apiUrl: '/api',
  loading: false,
  error: null
})

export function useApi() {
  return useContext(APIContext)
}

function Navbar() {
  const navigate = useNavigate()
  
  return (
    <nav style={{
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border)',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <div style={{
        maxWidth: 1200,
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: 64
      }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <svg width="32" height="32" viewBox="0 0 100 100">
            <defs>
              <linearGradient id="logo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{stopColor:'#6366f1'}}/>
                <stop offset="100%" style={{stopColor:'#8b5cf6'}}/>
              </linearGradient>
            </defs>
            <circle cx="50" cy="50" r="30" fill="none" stroke="url(#logo-grad)" strokeWidth="6"/>
            <circle cx="50" cy="50" r="15" fill="url(#logo-grad)"/>
            <circle cx="50" cy="50" r="5" fill="#22c55e"/>
          </svg>
          <span style={{ fontSize: 20, fontWeight: 700 }}>LoadPilot</span>
        </Link>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Link to="/" className="btn btn-ghost btn-sm">
            Dashboard
          </Link>
          <button 
            onClick={() => navigate('/test/new')}
            className="btn btn-primary btn-sm"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            New Test
          </button>
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh' }}>
        <Navbar />
        <main style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/test/new" element={<NewTest />} />
            <Route path="/test/:id" element={<TestResults />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
