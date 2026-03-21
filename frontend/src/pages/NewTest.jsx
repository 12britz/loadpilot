import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const CLOUD_PROVIDERS = [
  { value: 'aws', label: 'AWS' },
  { value: 'gcp', label: 'Google Cloud' },
  { value: 'azure', label: 'Azure' },
]

const REGIONS = {
  aws: [
    { value: 'us-east-1', label: 'US East (N. Virginia)' },
    { value: 'us-west-2', label: 'US West (Oregon)' },
    { value: 'eu-west-1', label: 'EU (Ireland)' },
    { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)' },
  ],
  gcp: [
    { value: 'us-central1', label: 'US Central (Iowa)' },
    { value: 'us-east1', label: 'US East (South Carolina)' },
  ],
  azure: [
    { value: 'eastus', label: 'East US' },
  ],
}

function FormSection({ title, children }) {
  return (
    <div style={{ marginBottom: 32 }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20, color: 'var(--text-primary)' }}>
        {title}
      </h3>
      {children}
    </div>
  )
}

function RangeInput({ label, min, max, step = 1, value, onChange, unit = '' }) {
  return (
    <div className="input-group">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <label>{label}</label>
        <span style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: 14, 
          color: 'var(--primary)',
          background: 'rgba(99, 102, 241, 0.1)',
          padding: '4px 10px',
          borderRadius: 6
        }}>
          {value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{
          width: '100%',
          height: 6,
          borderRadius: 3,
          background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${((value - min) / (max - min)) * 100}%, var(--border) ${((value - min) / (max - min)) * 100}%, var(--border) 100%)`,
          appearance: 'none',
          cursor: 'pointer',
          outline: 'none'
        }}
      />
      <style>{`
        input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: var(--primary);
          cursor: pointer;
          border: 2px solid var(--bg-primary);
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }
      `}</style>
    </div>
  )
}

function DualRange({ label, min, max, step = 1, value, onChange, unit = '' }) {
  const [localMin, localMax] = value
  
  return (
    <div className="input-group">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <label>{label}</label>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ 
            fontFamily: 'var(--font-mono)', 
            fontSize: 14, 
            color: 'var(--primary)',
            background: 'rgba(99, 102, 241, 0.1)',
            padding: '4px 10px',
            borderRadius: 6
          }}>
            {localMin}{unit}
          </span>
          <span style={{ color: 'var(--text-muted)' }}>→</span>
          <span style={{ 
            fontFamily: 'var(--font-mono)', 
            fontSize: 14, 
            color: 'var(--primary)',
            background: 'rgba(99, 102, 241, 0.1)',
            padding: '4px 10px',
            borderRadius: 6
          }}>
            {localMax}{unit}
          </span>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 16 }}>
        <input
          type="range"
          min={min}
          max={localMax}
          step={step}
          value={localMin}
          onChange={(e) => onChange([Number(e.target.value), localMax])}
          style={{ flex: 1, height: 6, borderRadius: 3, appearance: 'none', cursor: 'pointer' }}
        />
        <input
          type="range"
          min={localMin}
          max={max}
          step={step}
          value={localMax}
          onChange={(e) => onChange([localMin, Number(e.target.value)])}
          style={{ flex: 1, height: 6, borderRadius: 3, appearance: 'none', cursor: 'pointer' }}
        />
      </div>
    </div>
  )
}

function ConfigSummary({ formData }) {
  const cpuCount = Math.ceil((formData.cpuMax - formData.cpuMin) / formData.cpuStep) + 1
  const memCount = Math.ceil((formData.memoryMax - formData.memoryMin) / formData.memoryStep) + 1
  const replicaCount = formData.replicaMax - formData.replicaMin + 1
  const totalConfigs = cpuCount * memCount * replicaCount
  
  return (
    <div style={{
      background: 'var(--bg-tertiary)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      padding: 20,
    }}>
      <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: 'var(--text-secondary)' }}>
        Test Matrix Summary
      </h4>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
        <div style={{ textAlign: 'center', padding: 12, background: 'var(--bg-secondary)', borderRadius: 8 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)' }}>{cpuCount}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>CPU Options</div>
        </div>
        <div style={{ textAlign: 'center', padding: 12, background: 'var(--bg-secondary)', borderRadius: 8 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)' }}>{memCount}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Memory Options</div>
        </div>
        <div style={{ textAlign: 'center', padding: 12, background: 'var(--bg-secondary)', borderRadius: 8 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)' }}>{replicaCount}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Replica Options</div>
        </div>
        <div style={{ textAlign: 'center', padding: 12, background: 'rgba(99, 102, 241, 0.1)', borderRadius: 8 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)' }}>{totalConfigs}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Total Configs</div>
        </div>
      </div>
    </div>
  )
}

export default function NewTest() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    cloudProvider: 'aws',
    region: 'us-east-1',
    cpuMin: 250,
    cpuMax: 2000,
    cpuStep: 250,
    memoryMin: 256,
    memoryMax: 2048,
    memoryStep: 256,
    replicaMin: 1,
    replicaMax: 5,
    rampUp: 60,
    peak: 120,
    rampDown: 60,
    vusersMin: 100,
    vusersMax: 1000,
    targetRps: 1000,
  })
  
  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }
  
  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      alert('Please enter a test name')
      return
    }
    
    setLoading(true)
    
    try {
      const res = await fetch('/api/tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          cloud_provider: formData.cloudProvider,
          region: formData.region,
          resource_config: {
            cpu_min: formData.cpuMin,
            cpu_max: formData.cpuMax,
            cpu_step: formData.cpuStep,
            memory_min: formData.memoryMin,
            memory_max: formData.memoryMax,
            memory_step: formData.memoryStep,
          },
          replica_config: {
            min: formData.replicaMin,
            max: formData.replicaMax,
          },
          traffic_config: {
            ramp_up: formData.rampUp,
            peak: formData.peak,
            ramp_down: formData.rampDown,
            vusers_min: formData.vusersMin,
            vusers_max: formData.vusersMax,
            target_rps: formData.targetRps,
          },
        }),
      })
      
      const test = await res.json()
      
      const runRes = await fetch(`/api/tests/${test.id}/run`, { method: 'POST' })
      await runRes.json()
      
      navigate(`/test/${test.id}`)
    } catch (err) {
      console.error('Failed to create test:', err)
      alert('Failed to create test')
    } finally {
      setLoading(false)
    }
  }
  
  const regions = REGIONS[formData.cloudProvider] || REGIONS.aws
  
  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="page-header">
        <h1>New Performance Test</h1>
        <p>Configure and run automated pod optimization tests</p>
      </div>
      
      <div className="card" style={{ marginBottom: 24 }}>
        <FormSection title="Basic Information">
          <div className="grid grid-2" style={{ gap: 20 }}>
            <div className="input-group">
              <label>Test Name</label>
              <input
                type="text"
                className="input"
                placeholder="e.g., api-gateway-perf"
                value={formData.name}
                onChange={(e) => updateField('name', e.target.value)}
              />
            </div>
            <div className="input-group">
              <label>Cloud Provider</label>
              <select 
                className="select"
                value={formData.cloudProvider}
                onChange={(e) => {
                  updateField('cloudProvider', e.target.value)
                  updateField('region', REGIONS[e.target.value][0].value)
                }}
                style={{ width: '100%' }}
              >
                {CLOUD_PROVIDERS.map(p => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div className="input-group">
              <label>Region</label>
              <select 
                className="select"
                value={formData.region}
                onChange={(e) => updateField('region', e.target.value)}
                style={{ width: '100%' }}
              >
                {regions.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
          </div>
        </FormSection>
        
        <FormSection title="CPU Configuration">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <DualRange
              label="CPU Range (millicores)"
              min={100}
              max={4000}
              step={100}
              value={[formData.cpuMin, formData.cpuMax]}
              onChange={([min, max]) => {
                updateField('cpuMin', min)
                updateField('cpuMax', max)
              }}
              unit="m"
            />
            <RangeInput
              label="CPU Step"
              min={100}
              max={500}
              step={50}
              value={formData.cpuStep}
              onChange={(v) => updateField('cpuStep', v)}
              unit="m"
            />
          </div>
        </FormSection>
        
        <FormSection title="Memory Configuration">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <DualRange
              label="Memory Range (MB)"
              min={128}
              max={8192}
              step={128}
              value={[formData.memoryMin, formData.memoryMax]}
              onChange={([min, max]) => {
                updateField('memoryMin', min)
                updateField('memoryMax', max)
              }}
              unit="Mi"
            />
            <RangeInput
              label="Memory Step"
              min={128}
              max={1024}
              step={128}
              value={formData.memoryStep}
              onChange={(v) => updateField('memoryStep', v)}
              unit="Mi"
            />
          </div>
        </FormSection>
        
        <FormSection title="Replica Configuration">
          <DualRange
            label="Replica Range"
            min={1}
            max={20}
            step={1}
            value={[formData.replicaMin, formData.replicaMax]}
            onChange={([min, max]) => {
              updateField('replicaMin', min)
              updateField('replicaMax', max)
            }}
            unit=""
          />
        </FormSection>
        
        <FormSection title="Traffic Pattern">
          <div className="grid grid-3" style={{ gap: 16 }}>
            <div className="input-group">
              <label>Ramp Up (sec)</label>
              <input
                type="number"
                className="input"
                value={formData.rampUp}
                onChange={(e) => updateField('rampUp', Number(e.target.value))}
              />
            </div>
            <div className="input-group">
              <label>Peak Duration (sec)</label>
              <input
                type="number"
                className="input"
                value={formData.peak}
                onChange={(e) => updateField('peak', Number(e.target.value))}
              />
            </div>
            <div className="input-group">
              <label>Ramp Down (sec)</label>
              <input
                type="number"
                className="input"
                value={formData.rampDown}
                onChange={(e) => updateField('rampDown', Number(e.target.value))}
              />
            </div>
            <div className="input-group">
              <label>Min Virtual Users</label>
              <input
                type="number"
                className="input"
                value={formData.vusersMin}
                onChange={(e) => updateField('vusersMin', Number(e.target.value))}
              />
            </div>
            <div className="input-group">
              <label>Max Virtual Users</label>
              <input
                type="number"
                className="input"
                value={formData.vusersMax}
                onChange={(e) => updateField('vusersMax', Number(e.target.value))}
              />
            </div>
            <div className="input-group">
              <label>Target RPS</label>
              <input
                type="number"
                className="input"
                value={formData.targetRps}
                onChange={(e) => updateField('targetRps', Number(e.target.value))}
              />
            </div>
          </div>
        </FormSection>
        
        <ConfigSummary formData={formData} />
      </div>
      
      <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
        <button 
          className="btn btn-secondary"
          onClick={() => navigate('/')}
          disabled={loading}
        >
          Cancel
        </button>
        <button 
          className="btn btn-primary btn-lg"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="loading-spinner" />
              Creating Test...
            </>
          ) : (
            <>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
              Run Test
            </>
          )}
        </button>
      </div>
    </div>
  )
}
