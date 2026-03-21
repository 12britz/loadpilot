import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

const API = '/api'

function StatusBadge({ status }) {
  const colors = {
    pending: { bg: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b' },
    running: { bg: 'rgba(99, 102, 241, 0.2)', color: '#6366f1' },
    completed: { bg: 'rgba(34, 197, 94, 0.2)', color: '#22c55e' },
    failed: { bg: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' },
    stopped: { bg: 'rgba(148, 163, 184, 0.2)', color: '#94a3b8' },
    paused: { bg: 'rgba(251, 191, 36, 0.2)', color: '#fbbf24' },
  }
  const c = colors[status] || colors.pending
  
  return (
    <span style={{
      padding: '4px 12px',
      borderRadius: 20,
      fontSize: 12,
      fontWeight: 500,
      background: c.bg,
      color: c.color,
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
    }}>
      {status === 'running' && <span className="loading-spinner" style={{ width: 10, height: 10 }} />}
      {status}
    </span>
  )
}

function Card({ title, children, actions }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border)',
      borderRadius: 16,
      padding: 24,
      marginBottom: 24,
    }}>
      {title && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600 }}>{title}</h3>
          {actions}
        </div>
      )}
      {children}
    </div>
  )
}

function Button({ children, onClick, variant = 'primary', disabled, size = 'md' }) {
  const styles = {
    primary: { bg: 'var(--primary)', color: 'white' },
    secondary: { bg: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border)' },
    success: { bg: '#22c55e', color: 'white' },
    danger: { bg: '#ef4444', color: 'white' },
  }
  const s = styles[variant]
  const sizes = { sm: { padding: '6px 12px', fontSize: 12 }, md: { padding: '10px 16px', fontSize: 14 }, lg: { padding: '14px 24px', fontSize: 16 } }
  
  return (
    <button onClick={onClick} disabled={disabled} style={{
      ...s, ...sizes[size], borderRadius: 10, fontWeight: 500, cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1, display: 'inline-flex', alignItems: 'center', gap: 8, border: s.border || 'none',
    }}>
      {children}
    </button>
  )
}

function Input({ label, type = 'text', value, onChange, placeholder, min, max, step }) {
  return (
    <div style={{ marginBottom: 16 }}>
      {label && <label style={{ display: 'block', fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6 }}>{label}</label>}
      <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} min={min} max={max} step={step} style={{
        width: '100%', padding: '10px 14px', background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 10, color: 'var(--text-primary)', fontSize: 14,
      }} />
    </div>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <div style={{ marginBottom: 16 }}>
      {label && <label style={{ display: 'block', fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6 }}>{label}</label>}
      <select value={value} onChange={e => onChange(e.target.value)} style={{
        width: '100%', padding: '10px 14px', background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 10, color: 'var(--text-primary)', fontSize: 14,
      }}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

function FileInput({ label, onChange, accept }) {
  const inputRef = useRef()
  const [fileName, setFileName] = useState('')
  
  const handleChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setFileName(file.name)
      onChange(file)
    }
  }
  
  return (
    <div style={{ marginBottom: 16 }}>
      {label && <label style={{ display: 'block', fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6 }}>{label}</label>}
      <div onClick={() => inputRef.current?.click()} style={{
        padding: 24, background: 'var(--bg-tertiary)', border: '2px dashed var(--border)', borderRadius: 10, textAlign: 'center', cursor: 'pointer',
      }}>
        <input ref={inputRef} type="file" accept={accept} onChange={handleChange} style={{ display: 'none' }} />
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ margin: '0 auto 8px', opacity: 0.5 }}>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        {fileName ? (
          <div style={{ fontSize: 14, color: 'var(--success)' }}>{fileName}</div>
        ) : (
          <>
            <div style={{ fontSize: 14 }}>Click to upload or drag and drop</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>JMX files</div>
          </>
        )}
      </div>
    </div>
  )
}

function MetricCard({ label, value, unit, color = '#6366f1' }) {
  return (
    <div style={{ background: 'var(--bg-tertiary)', borderRadius: 12, padding: 16, textAlign: 'center' }}>
      <div style={{ fontSize: 24, fontWeight: 700, color }}>{value}{unit}</div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{label}</div>
    </div>
  )
}

function JmxTestForm({ onSubmit, loading }) {
  const [form, setForm] = useState({ name: '', cloudProvider: 'aws', region: 'us-east-1', threads: 100, rampUp: 60, duration: 300, jmxFile: null })
  
  const regions = {
    aws: [{ value: 'us-east-1', label: 'US East (N. Virginia)' }, { value: 'us-west-2', label: 'US West (Oregon)' }, { value: 'eu-west-1', label: 'EU (Ireland)' }],
    gcp: [{ value: 'us-central1', label: 'US Central' }],
    azure: [{ value: 'eastus', label: 'East US' }],
  }
  
  const handleSubmit = () => {
    if (!form.name || !form.jmxFile) { alert('Please enter name and upload JMX file'); return }
    onSubmit(form)
  }
  
  return (
    <div>
      <div className="grid grid-2">
        <Input label="Test Name" value={form.name} onChange={v => setForm({...form, name: v})} placeholder="e.g., api-load-test" />
        <Select label="Cloud Provider" value={form.cloudProvider} onChange={v => setForm({...form, cloudProvider: v, region: regions[v][0].value})} options={[{ value: 'aws', label: 'AWS' }, { value: 'gcp', label: 'Google Cloud' }, { value: 'azure', label: 'Azure' }]} />
      </div>
      <Select label="Region" value={form.region} onChange={v => setForm({...form, region: v})} options={regions[form.cloudProvider]} />
      <div className="grid grid-3">
        <Input label="Threads (VUs)" type="number" value={form.threads} onChange={v => setForm({...form, threads: parseInt(v) || 100})} />
        <Input label="Ramp-up (sec)" type="number" value={form.rampUp} onChange={v => setForm({...form, rampUp: parseInt(v) || 60})} />
        <Input label="Duration (sec)" type="number" value={form.duration} onChange={v => setForm({...form, duration: parseInt(v) || 300})} />
      </div>
      <FileInput label="JMeter Test Plan (.jmx)" accept=".jmx,.xml" onChange={file => setForm({...form, jmxFile: file})} />
      <Button onClick={handleSubmit} disabled={loading}>{loading ? <span className="loading-spinner" /> : 'Run Test'}</Button>
    </div>
  )
}

function MatrixTestForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    name: '', cloudProvider: 'aws', cpuMin: 250, cpuMax: 2000, cpuStep: 250,
    memoryMin: 256, memoryMax: 4096, memoryStep: 512, replicasMin: 1, replicasMax: 5,
  })
  
  const cpuCount = Math.ceil((form.cpuMax - form.cpuMin) / form.cpuStep) + 1
  const memCount = Math.ceil((form.memoryMax - form.memoryMin) / form.memoryStep) + 1
  const repCount = form.replicasMax - form.replicasMin + 1
  const totalConfigs = cpuCount * memCount * repCount
  
  const handleSubmit = () => {
    if (!form.name) { alert('Please enter test name'); return }
    onSubmit(form)
  }
  
  return (
    <div>
      <div className="grid grid-2">
        <Input label="Test Name" value={form.name} onChange={v => setForm({...form, name: v})} placeholder="e.g., pod-optimization" />
        <Select label="Cloud Provider" value={form.cloudProvider} onChange={v => setForm({...form, cloudProvider: v})} options={[{ value: 'aws', label: 'AWS' }, { value: 'gcp', label: 'Google Cloud' }, { value: 'azure', label: 'Azure' }]} />
      </div>
      <div style={{ padding: 16, background: 'var(--bg-tertiary)', borderRadius: 12, marginBottom: 16 }}>
        <h4 style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>CPU (millicores)</h4>
        <div className="grid grid-3">
          <Input label="Min" type="number" value={form.cpuMin} onChange={v => setForm({...form, cpuMin: parseInt(v)})} />
          <Input label="Max" type="number" value={form.cpuMax} onChange={v => setForm({...form, cpuMax: parseInt(v)})} />
          <Input label="Step" type="number" value={form.cpuStep} onChange={v => setForm({...form, cpuStep: parseInt(v)})} />
        </div>
      </div>
      <div style={{ padding: 16, background: 'var(--bg-tertiary)', borderRadius: 12, marginBottom: 16 }}>
        <h4 style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>Memory (MB)</h4>
        <div className="grid grid-3">
          <Input label="Min" type="number" value={form.memoryMin} onChange={v => setForm({...form, memoryMin: parseInt(v)})} />
          <Input label="Max" type="number" value={form.memoryMax} onChange={v => setForm({...form, memoryMax: parseInt(v)})} />
          <Input label="Step" type="number" value={form.memoryStep} onChange={v => setForm({...form, memoryStep: parseInt(v)})} />
        </div>
      </div>
      <div style={{ padding: 16, background: 'var(--bg-tertiary)', borderRadius: 12, marginBottom: 16 }}>
        <h4 style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>Replicas</h4>
        <div className="grid grid-2">
          <Input label="Min" type="number" value={form.replicasMin} onChange={v => setForm({...form, replicasMin: parseInt(v)})} />
          <Input label="Max" type="number" value={form.replicasMax} onChange={v => setForm({...form, replicasMax: parseInt(v)})} />
        </div>
      </div>
      <div style={{ padding: 20, background: 'rgba(99, 102, 241, 0.1)', borderRadius: 12, marginBottom: 16, textAlign: 'center' }}>
        <div style={{ fontSize: 36, fontWeight: 700, color: 'var(--primary)' }}>{totalConfigs}</div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Total Configurations</div>
      </div>
      <Button onClick={handleSubmit} disabled={loading}>{loading ? <span className="loading-spinner" /> : 'Run Matrix Test'}</Button>
    </div>
  )
}

function InteractiveTestForm({ onSubmit, loading }) {
  const [form, setForm] = useState({ name: '', threads: 100, duration: 300, jmxFile: null })
  
  const handleSubmit = () => {
    if (!form.name || !form.jmxFile) { alert('Please enter name and upload JMX file'); return }
    onSubmit(form)
  }
  
  return (
    <div>
      <Input label="Test Name" value={form.name} onChange={v => setForm({...form, name: v})} placeholder="e.g., interactive-load" />
      <div className="grid grid-2">
        <Input label="Threads (VUs)" type="number" value={form.threads} onChange={v => setForm({...form, threads: parseInt(v) || 100})} />
        <Input label="Duration (sec)" type="number" value={form.duration} onChange={v => setForm({...form, duration: parseInt(v) || 300})} />
      </div>
      <FileInput label="JMeter Test Plan (.jmx)" accept=".jmx,.xml" onChange={file => setForm({...form, jmxFile: file})} />
      <div style={{ padding: 12, background: 'rgba(99, 102, 241, 0.1)', borderRadius: 10, marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)' }}>
        Interactive mode allows real-time control: stop, pause, scale, and get AI recommendations.
      </div>
      <Button onClick={handleSubmit} disabled={loading}>{loading ? <span className="loading-spinner" /> : 'Start Interactive Test'}</Button>
    </div>
  )
}

function InteractiveMonitor({ testId }) {
  const [status, setStatus] = useState(null)
  const [aiRecommendation, setAiRecommendation] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const intervalRef = useRef()
  
  useEffect(() => {
    fetchStatus()
    intervalRef.current = setInterval(fetchStatus, 2000)
    return () => clearInterval(intervalRef.current)
  }, [testId])
  
  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API}/load-test/${testId}/status`)
      if (res.ok) {
        const data = await res.json()
        setStatus(data)
      }
    } catch (e) { console.error(e) }
  }
  
  const handleControl = async (action) => {
    await fetch(`${API}/load-test/${testId}/${action}`, { method: 'POST' })
    fetchStatus()
  }
  
  const getAiAdvice = async () => {
    setAiLoading(true)
    try {
      const res = await fetch(`${API}/load-test/${testId}/ai-decide`, { method: 'POST' })
      const data = await res.json()
      setAiRecommendation(data.ai_recommendation)
    } catch (e) { console.error(e) }
    setAiLoading(false)
  }
  
  if (!status) return <div className="skeleton" style={{ height: 300 }} />
  
  return (
    <div style={{ background: 'var(--bg-secondary)', border: '2px solid var(--primary)', borderRadius: 16, padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h3 style={{ fontSize: 18, fontWeight: 600 }}>Live Test Monitor</h3>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'monospace' }}>{testId.substring(0, 8)}...</div>
        </div>
        <StatusBadge status={status.status} />
      </div>
      
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Progress</span>
          <span style={{ fontSize: 13, fontWeight: 600 }}>{status.progress_percent?.toFixed(1)}%</span>
        </div>
        <div style={{ height: 8, background: 'var(--bg-tertiary)', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{ width: `${status.progress_percent}%`, height: '100%', background: 'linear-gradient(90deg, var(--primary), #8b5cf6)', transition: 'width 0.3s' }} />
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
          {status.elapsed_seconds}s / {status.total_seconds}s • Phase: {status.phase}
        </div>
      </div>
      
      <div className="grid grid-4" style={{ marginBottom: 20 }}>
        <MetricCard label="Current Threads" value={status.current_threads || 0} color="#6366f1" />
        <MetricCard label="Target" value={status.target_threads || 0} color="#94a3b8" />
        <MetricCard label="P99 Latency" value={status.current_metrics?.latency_p99?.toFixed(0) || '-'} unit="ms" color="#f59e0b" />
        <MetricCard label="Error Rate" value={status.current_metrics?.error_rate?.toFixed(1) || '0'} unit="%" color="#22c55e" />
      </div>
      
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        {status.status === 'running' && (
          <>
            <Button variant="danger" size="sm" onClick={() => handleControl('stop')}>Stop</Button>
            <Button variant="secondary" size="sm" onClick={() => handleControl('pause')}>Pause</Button>
            <Button variant="success" size="sm" onClick={() => handleControl('increase')}>+25% Load</Button>
            <Button variant="secondary" size="sm" onClick={() => handleControl('decrease')}>-25% Load</Button>
          </>
        )}
        {status.status === 'paused' && <Button variant="success" size="sm" onClick={() => handleControl('resume')}>Resume</Button>}
        {status.status === 'completed' && (
          <Button variant="success" size="sm" onClick={getAiAdvice} disabled={aiLoading}>Get AI Summary</Button>
        )}
        <Button variant="secondary" size="sm" onClick={getAiAdvice} disabled={aiLoading}>
          {aiLoading ? <span className="loading-spinner" /> : '🤖 AI Advice'}
        </Button>
      </div>
      
      {aiRecommendation && (
        <div style={{ padding: 16, background: 'var(--bg-tertiary)', borderRadius: 12, fontSize: 13, lineHeight: 1.6 }}>
          <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--primary)' }}>AI Recommendation</div>
          <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'inherit' }}>{aiRecommendation}</pre>
        </div>
      )}
    </div>
  )
}

function TestList({ tests, onSelect }) {
  if (!tests?.length) return (
    <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
      No tests yet. Create one above!
    </div>
  )
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {tests.map(test => (
        <div key={test.id} onClick={() => onSelect(test)} style={{
          padding: 16, background: 'var(--bg-tertiary)', borderRadius: 12, cursor: 'pointer',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>{test.name}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {test.test_type === 'jmx' ? 'JMeter' : 'Matrix'} • {test.total_configs} configs
            </div>
          </div>
          <StatusBadge status={test.status} />
        </div>
      ))}
    </div>
  )
}

function SystemStatus({ onOpenSettings }) {
  const [jmeter, setJmeter] = useState(null)
  const [ollama, setOllama] = useState(null)
  
  useEffect(() => {
    fetch(`${API}/jmeter/check`).then(r => r.json()).then(setJmeter)
    fetch(`${API}/ai/models`).then(r => r.json()).then(setOllama).catch(() => setOllama({available: false}))
  }, [])
  
  return (
    <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap', alignItems: 'center' }}>
      <div style={{ padding: '8px 16px', background: jmeter?.installed ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', borderRadius: 20, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: jmeter?.installed ? '#22c55e' : '#ef4444' }} />
        JMeter: {jmeter?.installed ? 'Ready' : 'Not installed'}
      </div>
      <div style={{ padding: '8px 16px', background: ollama?.available ? 'rgba(34, 197, 94, 0.1)' : 'rgba(245, 158, 11, 0.1)', borderRadius: 20, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: ollama?.available ? '#22c55e' : '#f59e0b' }} />
        Ollama: {ollama?.available ? `✅ ${ollama.current_model || 'llama3.2'}` : '⚠️ Not running'}
        {ollama?.available && ollama?.models?.length > 1 && (
          <button onClick={onOpenSettings} style={{ marginLeft: 8, padding: '2px 8px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: 8, fontSize: 11, cursor: 'pointer' }}>
            Change Model
          </button>
        )}
      </div>
      <button onClick={onOpenSettings} style={{ padding: '8px 16px', background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 20, fontSize: 13, cursor: 'pointer', color: 'var(--text-secondary)' }}>
        ⚙️ Settings
      </button>
    </div>
  )
}

function SettingsModal({ isOpen, onClose }) {
  const [ollama, setOllama] = useState(null)
  const [selectedModel, setSelectedModel] = useState('')
  const [saving, setSaving] = useState(false)
  
  useEffect(() => {
    if (isOpen) {
      fetch(`${API}/ai/models`).then(r => r.json()).then(data => {
        setOllama(data)
        setSelectedModel(data.current_model || '')
      })
    }
  }, [isOpen])
  
  const handleSave = async () => {
    if (!selectedModel) return
    setSaving(true)
    try {
      await fetch(`${API}/ai/model?model=${selectedModel}`, { method: 'POST' })
      onClose()
    } catch (e) {
      console.error(e)
      alert('Failed to save')
    }
    setSaving(false)
  }
  
  if (!isOpen) return null
  
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg-secondary)', borderRadius: 16, padding: 32, width: '100%', maxWidth: 500,
        border: '1px solid var(--border)'
      }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ fontSize: 20, fontWeight: 600 }}>⚙️ Settings</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: 24, cursor: 'pointer' }}>×</button>
        </div>
        
        <div style={{ marginBottom: 24 }}>
          <h4 style={{ fontSize: 14, fontWeight: 500, marginBottom: 12, color: 'var(--text-secondary)' }}>AI Model (Ollama)</h4>
          
          {ollama?.available ? (
            <>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
                Select an AI model for generating recommendations. Make sure Ollama is running with the desired model.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {ollama.models?.map(model => (
                  <label key={model} style={{
                    padding: 12, background: selectedModel === model ? 'rgba(99, 102, 241, 0.2)' : 'var(--bg-tertiary)',
                    borderRadius: 10, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12,
                    border: selectedModel === model ? '2px solid var(--primary)' : '2px solid transparent'
                  }}>
                    <input type="radio" name="model" value={model} checked={selectedModel === model} onChange={e => setSelectedModel(e.target.value)} />
                    <span style={{ fontWeight: 500 }}>{model}</span>
                  </label>
                ))}
              </div>
              {ollama.models?.length === 0 && (
                <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>
                  No models available. Run: <code>ollama pull llama3.2</code>
                </div>
              )}
            </>
          ) : (
            <div style={{ padding: 20, background: 'rgba(245, 158, 11, 0.1)', borderRadius: 10, textAlign: 'center' }}>
              <p style={{ color: 'var(--warning)', marginBottom: 8 }}>Ollama is not running</p>
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Run these commands in a terminal:<br/>
                <code>brew install ollama && ollama serve</code><br/>
                <code>ollama pull llama3.2</code>
              </p>
            </div>
          )}
        </div>
        
        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '10px 20px', background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 10, cursor: 'pointer' }}>Cancel</button>
          <button onClick={handleSave} disabled={!ollama?.available || saving} style={{
            padding: '10px 20px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: 10, cursor: 'pointer', opacity: (!ollama?.available || saving) ? 0.5 : 1
          }}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('jmx')
  const [tests, setTests] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [interactiveTestId, setInteractiveTestId] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const navigate = useNavigate()
  
  useEffect(() => { fetchTests() }, [])
  
  const fetchTests = async () => {
    try {
      const res = await fetch(`${API}/tests`)
      const data = await res.json()
      setTests(data)
    } catch (e) { console.error(e) }
    setLoading(false)
  }
  
  const runJmxTest = async (form) => {
    setSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('name', form.name)
      formData.append('cloud_provider', form.cloudProvider)
      formData.append('region', form.region)
      formData.append('threads', form.threads)
      formData.append('ramp_up', form.rampUp)
      formData.append('duration', form.duration)
      formData.append('jmx_file', form.jmxFile)
      const res = await fetch(`${API}/tests/jmx`, { method: 'POST', body: formData })
      const test = await res.json()
      await fetch(`${API}/tests/${test.id}/run-jmx`, { method: 'POST' })
      fetchTests()
    } catch (e) { console.error(e); alert('Failed') }
    setSubmitting(false)
  }
  
  const runMatrixTest = async (form) => {
    setSubmitting(true)
    try {
      const res = await fetch(`${API}/tests`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name, cloud_provider: form.cloudProvider,
          resource_config: { cpu_min: form.cpuMin, cpu_max: form.cpuMax, cpu_step: form.cpuStep, memory_min: form.memoryMin, memory_max: form.memoryMax, memory_step: form.memoryStep },
          replica_config: { min: form.replicasMin, max: form.replicasMax },
        }),
      })
      const test = await res.json()
      await fetch(`${API}/tests/${test.id}/run`, { method: 'POST' })
      fetchTests()
    } catch (e) { console.error(e); alert('Failed') }
    setSubmitting(false)
  }
  
  const startInteractive = async (form) => {
    setSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('name', form.name)
      formData.append('threads', form.threads)
      formData.append('duration', form.duration)
      formData.append('jmx_file', form.jmxFile)
      const res = await fetch(`${API}/load-test/start`, { method: 'POST', body: formData })
      const data = await res.json()
      setInteractiveTestId(data.test_id)
    } catch (e) { console.error(e); alert('Failed') }
    setSubmitting(false)
  }
  
  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>LoadPilot</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Automated load testing with AI-powered recommendations</p>
      </div>
      
      <SystemStatus onOpenSettings={() => setShowSettings(true)} />
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
      
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {['jmx', 'matrix', 'interactive'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            padding: '10px 20px', background: activeTab === tab ? 'var(--primary)' : 'var(--bg-tertiary)',
            color: activeTab === tab ? 'white' : 'var(--text-secondary)', border: 'none', borderRadius: 10, fontWeight: 500, cursor: 'pointer', textTransform: 'capitalize',
          }}>{tab === 'jmx' ? 'JMX Test' : tab === 'matrix' ? 'Matrix Test' : 'Interactive'}</button>
        ))}
      </div>
      
      <div className="grid" style={{ gridTemplateColumns: activeTab === 'interactive' && interactiveTestId ? '1fr' : '1fr 1fr', gap: 24 }}>
        <div>
          <Card title={activeTab === 'jmx' ? 'Run JMeter Test' : activeTab === 'matrix' ? 'Matrix Test' : 'Start Interactive Test'}>
            {activeTab === 'jmx' && <JmxTestForm onSubmit={runJmxTest} loading={submitting} />}
            {activeTab === 'matrix' && <MatrixTestForm onSubmit={runMatrixTest} loading={submitting} />}
            {activeTab === 'interactive' && <InteractiveTestForm onSubmit={startInteractive} loading={submitting} />}
          </Card>
        </div>
        <div>
          {activeTab === 'interactive' && interactiveTestId ? (
            <InteractiveMonitor testId={interactiveTestId} />
          ) : (
            <Card title="Recent Tests">
              {loading ? <div className="skeleton" style={{ height: 200 }} /> : <TestList tests={tests.slice(0, 5)} onSelect={t => navigate(`/test/${t.id}`)} />}
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
