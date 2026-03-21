import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, Legend
} from 'recharts'

const COLORS = {
  primary: '#6366f1',
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
}

function MetricBadge({ label, value, unit, threshold }) {
  let color = COLORS.success
  if (threshold) {
    if (value > threshold.danger) color = COLORS.danger
    else if (value > threshold.warning) color = COLORS.warning
  }
  
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 20, fontWeight: 700, color }}>{value}{unit}</div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</div>
    </div>
  )
}

function WinnerCard({ winner, test }) {
  if (!winner) return null
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%)',
      border: '2px solid var(--success)',
      borderRadius: 'var(--radius-lg)',
      padding: 24,
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{
        position: 'absolute',
        top: -20,
        right: -20,
        width: 100,
        height: 100,
        background: 'var(--success)',
        borderRadius: '50%',
        opacity: 0.1
      }} />
      
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <div style={{
          width: 40,
          height: 40,
          borderRadius: '50%',
          background: 'var(--success)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        <div>
          <div style={{ fontSize: 14, color: 'var(--success)', fontWeight: 600 }}>RECOMMENDED</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{test.name}</div>
        </div>
      </div>
      
      <div className="grid grid-3" style={{ gap: 24 }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>CPU</div>
          <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            {winner.config.cpu}m
          </div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Memory</div>
          <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            {winner.config.memory}Mi
          </div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Replicas</div>
          <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            {winner.config.replicas}
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', gap: 24 }}>
        <MetricBadge label="P99 Latency" value={winner.metrics.latency_p99} unit="ms" />
        <MetricBadge label="Throughput" value={winner.metrics.throughput} unit=" rps" />
        <MetricBadge label="Error Rate" value={winner.metrics.error_rate} unit="%" />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Monthly Cost</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.success }}>
            ${winner.cost_monthly}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Score</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.primary }}>
            {winner.score}/10
          </div>
        </div>
      </div>
    </div>
  )
}

function CostPerformanceChart({ results }) {
  const data = results.map(r => ({
    cost: r.cost_monthly,
    performance: Math.round(r.score * 10),
    latency: r.metrics.latency_p99,
    throughput: r.metrics.throughput,
    cpu: r.config.cpu,
    memory: r.config.memory,
    replicas: r.config.replicas,
    score: r.score,
  }))
  
  return (
    <div className="card">
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>Cost vs Performance</h3>
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis 
            type="number" 
            dataKey="cost" 
            name="Cost"
            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
            label={{ value: 'Monthly Cost ($)', position: 'bottom', fill: 'var(--text-muted)' }}
          />
          <YAxis 
            type="number" 
            dataKey="score" 
            name="Score"
            domain={[0, 10]}
            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
            label={{ value: 'Score', angle: -90, position: 'left', fill: 'var(--text-muted)' }}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: 8,
            }}
            labelStyle={{ color: 'var(--text-primary)' }}
            formatter={(value, name) => {
              if (name === 'cost') return [`$${value}`, 'Cost']
              if (name === 'score') return [value, 'Score']
              return [value, name]
            }}
            labelFormatter={() => ''}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const d = payload[0].payload
              return (
                <div style={{ padding: 12, fontSize: 13 }}>
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>{d.cpu}m / {d.memory}Mi / {d.replicas}r</div>
                  <div>Cost: <span style={{ color: COLORS.warning }}>${d.cost}</span></div>
                  <div>Score: <span style={{ color: COLORS.primary }}>{d.score}</span></div>
                  <div>P99: <span>{d.latency}ms</span></div>
                  <div>RPS: <span>{d.throughput}</span></div>
                </div>
              )
            }}
          />
          <Scatter data={data}>
            {data.map((entry, index) => (
              <Cell 
                key={index} 
                fill={entry.score >= 8 ? COLORS.success : entry.score >= 6 ? COLORS.warning : COLORS.danger}
                opacity={0.8}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', gap: 20, justifyContent: 'center', marginTop: 16, fontSize: 12, color: 'var(--text-muted)' }}>
        <span><span style={{ color: COLORS.success }}>●</span> Good (8+)</span>
        <span><span style={{ color: COLORS.warning }}>●</span> Fair (6-8)</span>
        <span><span style={{ color: COLORS.danger }}>●</span> Poor (&lt;6)</span>
      </div>
    </div>
  )
}

function LatencyChart({ results }) {
  const sorted = [...results].sort((a, b) => a.config.cpu - b.config.cpu)
  
  const data = sorted.map(r => ({
    name: `${r.config.cpu}m/${r.config.memory}Mi`,
    p50: r.metrics.latency_p50,
    p95: r.metrics.latency_p95,
    p99: r.metrics.latency_p99,
  }))
  
  return (
    <div className="card">
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>Latency by Configuration</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
          <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
          <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} width={80} />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: 8,
            }}
          />
          <Legend />
          <Bar dataKey="p50" name="P50" fill={COLORS.success} />
          <Bar dataKey="p95" name="P95" fill={COLORS.warning} />
          <Bar dataKey="p99" name="P99" fill={COLORS.danger} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function ResultsTable({ results }) {
  const [sortField, setSortField] = useState('score')
  const [sortDir, setSortDir] = useState('desc')
  
  const sorted = [...results].sort((a, b) => {
    let aVal, bVal
    if (sortField.includes('.')) {
      const [parent, child] = sortField.split('.')
      aVal = a[parent][child]
      bVal = b[parent][child]
    } else {
      aVal = a[sortField]
      bVal = b[sortField]
    }
    return sortDir === 'asc' ? aVal - bVal : bVal - aVal
  })
  
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('desc')
    }
  }
  
  const SortIcon = ({ field }) => {
    if (sortField !== field) return null
    return sortDir === 'asc' ? ' ↑' : ' ↓'
  }
  
  return (
    <div className="card" style={{ overflowX: 'auto' }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>All Configurations</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => handleSort('config.cpu')}>
              CPU <SortIcon field="config.cpu" />
            </th>
            <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => handleSort('config.memory')}>
              Memory <SortIcon field="config.memory" />
            </th>
            <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => handleSort('config.replicas')}>
              Replicas <SortIcon field="config.replicas" />
            </th>
            <th style={{ textAlign: 'right', padding: '12px 8px', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => handleSort('metrics.latency_p99')}>
              P99 Latency <SortIcon field="metrics.latency_p99" />
            </th>
            <th style={{ textAlign: 'right', padding: '12px 8px', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => handleSort('metrics.throughput')}>
              Throughput <SortIcon field="metrics.throughput" />
            </th>
            <th style={{ textAlign: 'right', padding: '12px 8px', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => handleSort('metrics.error_rate')}>
              Error Rate <SortIcon field="metrics.error_rate" />
            </th>
            <th style={{ textAlign: 'right', padding: '12px 8px', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => handleSort('cost_monthly')}>
              Cost/mo <SortIcon field="cost_monthly" />
            </th>
            <th style={{ textAlign: 'right', padding: '12px 8px', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => handleSort('score')}>
              Score <SortIcon field="score" />
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr 
              key={r.id} 
              style={{ 
                borderBottom: '1px solid var(--border)',
                background: r.score >= 8 ? 'rgba(34, 197, 94, 0.05)' : 'transparent',
              }}
            >
              <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)' }}>{r.config.cpu}m</td>
              <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)' }}>{r.config.memory}Mi</td>
              <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)' }}>{r.config.replicas}</td>
              <td style={{ padding: '12px 8px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: r.metrics.latency_p99 > 200 ? COLORS.danger : r.metrics.latency_p99 > 100 ? COLORS.warning : COLORS.success }}>
                  {r.metrics.latency_p99}ms
                </span>
              </td>
              <td style={{ padding: '12px 8px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                {r.metrics.throughput.toFixed(0)}
              </td>
              <td style={{ padding: '12px 8px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: r.metrics.error_rate > 2 ? COLORS.danger : COLORS.success }}>
                  {r.metrics.error_rate}%
                </span>
              </td>
              <td style={{ padding: '12px 8px', textAlign: 'right', fontFamily: 'var(--font-mono)', color: COLORS.warning }}>
                ${r.cost_monthly}
              </td>
              <td style={{ padding: '12px 8px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                <span style={{ 
                  color: r.score >= 8 ? COLORS.success : r.score >= 6 ? COLORS.warning : COLORS.danger,
                  fontWeight: 600
                }}>
                  {r.score}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function TestResults() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchTest()
  }, [id])
  
  const fetchTest = async () => {
    try {
      const res = await fetch(`/api/tests/${id}`)
      if (!res.ok) throw new Error('Test not found')
      const json = await res.json()
      setData(json)
    } catch (err) {
      console.error('Failed to fetch test:', err)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div>
        <div className="skeleton" style={{ height: 40, width: 200, marginBottom: 24 }} />
        <div className="skeleton" style={{ height: 200, marginBottom: 24 }} />
        <div className="skeleton" style={{ height: 300, marginBottom: 24 }} />
        <div className="skeleton" style={{ height: 400 }} />
      </div>
    )
  }
  
  if (!data) {
    return (
      <div className="empty-state">
        <h3>Test not found</h3>
        <p>This test may have been deleted</p>
        <Link to="/" className="btn btn-primary" style={{ marginTop: 16 }}>Back to Dashboard</Link>
      </div>
    )
  }
  
  const statusColors = {
    pending: 'var(--warning)',
    running: 'var(--primary)',
    completed: 'var(--success)',
    failed: 'var(--danger)',
  }
  
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
        <button 
          onClick={() => navigate('/')}
          className="btn btn-ghost btn-sm"
          style={{ padding: 8 }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 style={{ fontSize: 24, fontWeight: 700 }}>{data.name}</h1>
            <span 
              className="badge"
              style={{ 
                background: `${statusColors[data.status]}20`,
                color: statusColors[data.status]
              }}
            >
              {data.status}
            </span>
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
            {data.cloud_provider.toUpperCase()} · {data.region} · {data.total_configs} configs tested
          </div>
        </div>
      </div>
      
      {data.status === 'completed' && (
        <>
          <WinnerCard winner={data.winner} test={data} />
          
          <div className="grid grid-2" style={{ marginTop: 24 }}>
            <CostPerformanceChart results={data.results} />
            <LatencyChart results={data.results} />
          </div>
          
          <div style={{ marginTop: 24 }}>
            <ResultsTable results={data.results} />
          </div>
        </>
      )}
      
      {data.status === 'running' && (
        <div className="card" style={{ textAlign: 'center', padding: 60 }}>
          <div className="loading-spinner" style={{ width: 40, height: 40, margin: '0 auto 16px' }} />
          <h3>Test in Progress</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: 8 }}>
            Running {data.total_configs} configuration tests...
          </p>
          <button onClick={fetchTest} className="btn btn-secondary" style={{ marginTop: 16 }}>
            Refresh
          </button>
        </div>
      )}
    </div>
  )
}
