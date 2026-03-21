# LoadPilot - Automated Kubernetes Pod Optimization

## Concept & Vision

LoadPilot automatically tests different Kubernetes pod configurations to find the optimal balance between cost and performance. Users define their service parameters and traffic patterns, and LoadPilot runs a series of benchmark tests, comparing latency, throughput, error rates, and monthly cloud costs across different CPU/memory/replica combinations.

**Personality**: Technical yet approachable. Results-driven with clear visualizations. "Your load testing copilot."

## Design Language

### Aesthetic Direction
Dark mode data dashboard inspired by Grafana/Datadog - professional observability tools that DevOps engineers trust.

### Color Palette
- **Background**: `#0f0f23` (deep navy)
- **Surface**: `#1a1a2e` (card backgrounds)
- **Border**: `#2d2d44` (subtle borders)
- **Primary**: `#6366f1` (indigo - actions)
- **Success**: `#22c55e` (green - good perf)
- **Warning**: `#f59e0b` (amber - high cost)
- **Danger**: `#ef4444` (red - poor perf)
- **Text Primary**: `#f1f5f9`
- **Text Secondary**: `#94a3b8`

### Typography
- **Headings**: Inter (700)
- **Body**: Inter (400, 500)
- **Mono**: JetBrains Mono (for metrics/code)

### Motion Philosophy
- Subtle pulse on running tests
- Smooth transitions on results (300ms ease)
- Progress bars with gradient fills
- Skeleton loaders for async content

## Layout & Structure

### Pages

1. **Dashboard** (`/`)
   - Quick stats cards (active tests, recommended configs, cost savings)
   - Recent test runs list
   - Quick start button

2. **New Test** (`/test/new`)
   - Service configuration form
   - Resource ranges (CPU/RAM)
   - Replica range
   - Traffic pattern config
   - Run button

3. **Test Results** (`/test/:id`)
   - Test configuration summary
   - Results matrix table
   - Winner recommendation card
   - Cost vs Performance scatter plot
   - Export/Apply buttons

### Responsive Strategy
Mobile-first, optimized for desktop (DevOps use desktop dashboards primarily)

## Features & Interactions

### Core Features

1. **Service Configuration**
   - Service name (required)
   - Cloud provider (AWS/GCP/Azure)
   - Region (dropdown)
   - Current config display

2. **Resource Ranges**
   - CPU: min/max with step (e.g., 250m-2000m, step 250m)
   - Memory: min/max with step (e.g., 256Mi-4Gi, step 256Mi)
   - Display as slider + input

3. **Replica Range**
   - Min replicas (1-10)
   - Max replicas (1-50)

4. **Traffic Pattern**
   - Ramp-up duration (seconds)
   - Peak duration (seconds)
   - Ramp-down duration (seconds)
   - Virtual users range
   - Target RPS

5. **Test Execution** (Simulated for MVP)
   - Generate all config combinations
   - Simulate load test results with realistic variance
   - Calculate cloud costs
   - Rank configs by score

6. **Results Analysis**
   - Config matrix with all metrics
   - Pareto frontier visualization
   - Winner recommendation with explanation
   - Cost savings calculation

### Interactions

- **Run Test**: Button → progress modal → redirect to results
- **Config Slider**: Drag → instant cost preview
- **Results Table**: Sortable columns, click row to expand
- **Winner Card**: Pulse animation, "Apply" CTA

### Edge Cases
- Empty ranges: Show validation error
- Single config: Still run, show "only option"
- All configs fail: Show error breakdown

## Component Inventory

### StatsCard
- Icon, label, value, trend
- States: loading (skeleton), loaded, error

### ConfigForm
- Input fields with labels and helper text
- Validation states: default, error, success

### ResourceSlider
- Dual-thumb range slider
- Value display above thumbs
- Step indicators

### TestProgressModal
- Current phase display
- Progress bar with percentage
- Config count (e.g., "Testing 12/24 configs")
- Cancel button

### ResultsTable
- Sortable headers
- Row hover highlight
- Winner row badge
- Expandable rows

### WinnerCard
- Config summary
- Key metrics highlighted
- "Apply Config" button
- Cost savings callout

### CostBadge
- Color-coded (green=low, yellow=medium, red=high)
- Monthly cost value

### MetricBadge
- Latency, throughput, error rate
- Color-coded performance

## Technical Approach

### Stack
- **Frontend**: React 18 + Vite
- **Backend**: FastAPI (Python)
- **Storage**: SQLite (file-based for MVP)
- **Charts**: Recharts

### API Endpoints

```
POST   /api/tests              - Create new test
GET    /api/tests              - List tests
GET    /api/tests/:id          - Get test details
GET    /api/tests/:id/results  - Get test results
DELETE /api/tests/:id          - Delete test
POST   /api/tests/:id/run      - Trigger test execution
```

### Data Model

**Test**
```python
{
  id: str (uuid)
  name: str
  cloud_provider: str
  region: str
  config: {
    cpu_min: int (millicores)
    cpu_max: int
    cpu_step: int
    memory_min: int (MB)
    memory_max: int
    memory_step: int
    replicas_min: int
    replicas_max: int
  }
  traffic: {
    ramp_up: int (seconds)
    peak: int
    ramp_down: int
    vusers_min: int
    vusers_max: int
    target_rps: int
  }
  status: "pending" | "running" | "completed" | "failed"
  created_at: datetime
  completed_at: datetime | null
}
```

**Result**
```python
{
  id: str
  test_id: str
  config: {
    cpu: int
    memory: int
    replicas: int
  }
  metrics: {
    latency_p50: float (ms)
    latency_p95: float
    latency_p99: float
    throughput: float (rps)
    error_rate: float (%)
  }
  cost_monthly: float ($)
  score: float (0-10)
  timestamp: datetime
}
```

### Cost Calculation

AWS EKS pricing:
- CPU: ~$0.0236/hour (c5.large)
- Memory: ~$0.0059/hour (GB)
- Plus $0.10/hour for EKS cluster

Monthly = (cpu_cost + memory_cost + cluster_cost) × 730 hours × replicas

### Scoring Formula

```
score = (latency_score × 0.3) + (throughput_score × 0.3) + (cost_score × 0.2) + (error_score × 0.2)

latency_score = max(0, 10 - (p99_latency / 100))
throughput_score = min(10, actual_rps / target_rps × 10)
cost_score = max(0, 10 - (monthly_cost / baseline_cost × 10))
error_score = max(0, 10 - (error_rate × 10))
```

### MVP Scope Limitations
- Simulated results (no actual k8s cluster)
- Single user (no auth)
- SQLite storage
- No CI/CD integration
- No GitOps output
