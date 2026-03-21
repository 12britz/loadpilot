# LoadPilot

**Automated Load Testing Platform for Kubernetes + JMeter + AI**

LoadPilot helps you find the optimal pod configuration for your Kubernetes workloads by testing different CPU/memory/replica combinations. It supports JMeter test plans and uses AI (Ollama) to provide intelligent recommendations.

---

## Features

| Feature | Description |
|---------|-------------|
| **Matrix Testing** | Test all CPU/memory/replica combinations to find optimal K8s config |
| **JMX Testing** | Execute existing JMeter test plans (.jmx files) |
| **AI Testing** | Interactive tests with real-time AI-powered recommendations |
| **Test Controls** | Start, stop, pause, resume, scale load dynamically |
| **Cost Analysis** | Real-time cloud cost calculation (AWS, GCP, Azure) |
| **Performance Scoring** | Weighted scoring based on latency, throughput, cost, errors |

---

## Prerequisites

| Component | Required | Install |
|-----------|----------|---------|
| Python | Yes | `3.9+` |
| Node.js | No | [nodejs.org](https://nodejs.org) |
| JMeter | No | [jmeter.apache.org](https://jmeter.apache.org) |
| Ollama | No | [ollama.ai](https://ollama.ai) |

---

## Quick Start

### 1. Install Dependencies

```bash
cd loadpilot/backend
pip install -r requirements.txt
```

### 2. Start Server

```bash
cd loadpilot
./start.sh
```

Server runs at: **http://localhost:8000**

### 3. Open API Docs

Visit **http://localhost:8000/docs** for interactive API documentation.

---

## Usage Examples

### Example 1: Find Optimal Kubernetes Config (Matrix Testing)

```bash
# Create a test that tries all combinations of CPU/RAM/replicas
curl -X POST http://localhost:8000/api/tests \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api-gateway",
    "cloud_provider": "aws",
    "region": "us-east-1",
    "resource_config": {
      "cpu_min": 250,
      "cpu_max": 2000,
      "cpu_step": 250,
      "memory_min": 256,
      "memory_max": 4096,
      "memory_step": 512
    },
    "replica_config": {
      "min": 1,
      "max": 5
    }
  }'

# Run the test
curl -X POST http://localhost:8000/api/tests/<TEST_ID>/run

# Get results
curl http://localhost:8000/api/tests/<TEST_ID>
```

### Example 2: Run JMeter Test Plan (JMX Testing)

```bash
# Upload and run a JMeter .jmx file
curl -X POST http://localhost:8000/api/tests/jmx \
  -F "name=api-load-test" \
  -F "cloud_provider=aws" \
  -F "threads=100" \
  -F "ramp_up=30" \
  -F "duration=120" \
  -F "jmx_file=@/path/to/test.jmx"

# Run the test
curl -X POST http://localhost:8000/api/tests/<TEST_ID>/run-jmx

# Get results
curl http://localhost:8000/api/tests/<TEST_ID>
```

### Example 3: Interactive Test with AI (Ollama)

```bash
# Start Ollama (in separate terminal)
ollama serve
ollama pull llama3.2

# Check if Ollama is available
curl http://localhost:8000/api/ai/check

# Start an interactive load test
curl -X POST http://localhost:8000/api/load-test/start \
  -F "name=interactive-test" \
  -F "threads=50" \
  -F "duration=300" \
  -F "jmx_file=@/path/to/test.jmx"

# Monitor status
curl http://localhost:8000/api/load-test/<TEST_ID>/status

# Increase load by 25%
curl -X POST http://localhost:8000/api/load-test/<TEST_ID>/increase

# Decrease load by 50%
curl -X POST http://localhost:8000/api/load-test/<TEST_ID>/decrease?percent=50

# Scale to specific threads
curl -X POST "http://localhost:8000/api/load-test/<TEST_ID>/scale?threads=200"

# Get AI recommendation based on current results
curl -X POST http://localhost:8000/api/load-test/<TEST_ID>/ai-decide

# Pause the test
curl -X POST http://localhost:8000/api/load-test/<TEST_ID>/pause

# Resume the test
curl -X POST http://localhost:8000/api/load-test/<TEST_ID>/resume

# Stop the test
curl -X POST http://localhost:8000/api/load-test/<TEST_ID>/stop
```

---

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Dashboard statistics |
| POST | `/api/tests` | Create matrix test |
| POST | `/api/tests/jmx` | Create JMX test |
| GET | `/api/tests` | List all tests |
| GET | `/api/tests/:id` | Get test details |
| POST | `/api/tests/:id/run` | Run matrix test |
| POST | `/api/tests/:id/run-jmx` | Run JMX test |
| DELETE | `/api/tests/:id` | Delete test |

### Interactive Test Controls

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/load-test/start` | Start interactive test |
| GET | `/api/load-test/:id/status` | Get test status |
| POST | `/api/load-test/:id/stop` | Stop test |
| POST | `/api/load-test/:id/pause` | Pause test |
| POST | `/api/load-test/:id/resume` | Resume test |
| POST | `/api/load-test/:id/scale` | Scale to specific threads |
| POST | `/api/load-test/:id/increase` | Increase load (%) |
| POST | `/api/load-test/:id/decrease` | Decrease load (%) |

### AI Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ai/check` | Check Ollama status |
| POST | `/api/ai/recommend/:id` | Get AI recommendations |
| POST | `/api/ai/summary/:id` | Get AI summary |
| POST | `/api/load-test/:id/ai-decide` | AI decision during test |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jmeter/check` | Check JMeter installation |

---

## Parameters

### Matrix Test Parameters

**Resource Config**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cpu_min` | int | 250 | Min CPU (millicores) |
| `cpu_max` | int | 2000 | Max CPU (millicores) |
| `cpu_step` | int | 250 | CPU increment |
| `memory_min` | int | 256 | Min memory (MB) |
| `memory_max` | int | 4096 | Max memory (MB) |
| `memory_step` | int | 256 | Memory increment |

**Replica Config**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min` | int | 1 | Min replicas |
| `max` | int | 5 | Max replicas |

### JMX Test Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Test name |
| `cloud_provider` | string | No | aws/gcp/azure |
| `region` | string | No | Cloud region |
| `threads` | int | No | Virtual users (default: 100) |
| `ramp_up` | int | No | Ramp-up time in sec (default: 60) |
| `duration` | int | No | Test duration in sec (default: 300) |
| `jmx_file` | file | Yes | JMeter .jmx file |

---

## Scoring System

Each configuration is scored 0-10:

```
score = (latency × 0.30) + (throughput × 0.30) + (cost × 0.20) + (errors × 0.20)
```

| Factor | Weight | Better = |
|--------|--------|-----------|
| Latency (P99) | 30% | Lower |
| Throughput (RPS) | 30% | Higher |
| Cost ($/mo) | 20% | Lower |
| Error Rate | 20% | Lower |

---

## Architecture

```
┌─────────────────────────────────────┐
│              Frontend               │
│        React + Vite + Recharts     │
└──────────────────┬────────────────┘
                   │ HTTP/REST
┌──────────────────▼────────────────┐
│              Backend               │
│         FastAPI + SQLite          │
├───────────────────────────────────┤
│  Matrix    │ Cost     │ JMX      │
│  Simulator │ Calculator│ Runner   │
│  AI Advisor│ Ollama   │ Controls  │
└───────────────────────────────────┘
```

---

## Project Structure

```
loadpilot/
├── README.md
├── SPEC.md
├── requirements.txt
├── setup.sh
├── start.sh
├── stop.sh
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── simulator.py          # Matrix test simulator
│   ├── cost_calculator.py    # Cloud cost calculation
│   ├── ollama_client.py      # AI/Ollama integration
│   └── test_runner.py        # Interactive test runner
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── index.css
        └── pages/
            ├── Dashboard.jsx
            ├── NewTest.jsx
            └── TestResults.jsx
```

---

## Installing Optional Components

### JMeter

```bash
# macOS
brew install jmeter

# Ubuntu/Debian
sudo apt install jmeter

# Manual
# Download from https://jmeter.apache.org/
```

### Ollama (for AI features)

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull a model
ollama pull llama3.2
```

---

## Roadmap

- [x] Matrix testing (CPU/RAM/Replicas)
- [x] JMX file execution
- [x] AI recommendations (Ollama)
- [x] Test controls (stop/start/scale)
- [ ] Real Kubernetes integration
- [ ] CI/CD pipeline hooks
- [ ] GitOps output (Helm/Kustomize)
- [ ] Historical trend analysis
- [ ] Slack/Teams notifications

---

## License

MIT
