"""
LoadPilot Backend API - FastAPI application
Supports matrix testing and JMX file execution
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3
import json
import uuid
import os
import shutil
import subprocess
import csv
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from models import (
    TestCreate, JmxTestCreate, TestResponse, TestDetailResponse, TestListResponse,
    TestDetailResponse, ResultResponse, JmxResultResponse, DashboardStats,
    ConfigSpec, Metrics, JmxMetrics, ResourceConfig, ReplicaConfig, TrafficConfig
)
from simulator import generate_config_matrix, simulate_metrics, calculate_score, find_winner
from cost_calculator import calculate_monthly_cost

DATABASE_PATH = "loadpilot.db"
UPLOAD_DIR = "uploads"
JMX_RESULTS_DIR = "jmx_results"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(JMX_RESULTS_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="LoadPilot API",
    description="Automated Kubernetes Pod Optimization + JMeter JMX Execution",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            test_type TEXT NOT NULL DEFAULT 'matrix',
            cloud_provider TEXT NOT NULL,
            region TEXT NOT NULL,
            resource_config TEXT,
            replica_config TEXT,
            traffic_config TEXT,
            jmx_config TEXT,
            jmx_filename TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            total_configs INTEGER DEFAULT 0,
            results_count INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id TEXT PRIMARY KEY,
            test_id TEXT NOT NULL,
            config TEXT,
            metrics TEXT,
            cost_monthly REAL NOT NULL,
            score REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (test_id) REFERENCES tests(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jmx_results (
            id TEXT PRIMARY KEY,
            test_id TEXT NOT NULL,
            jmx_filename TEXT NOT NULL,
            threads INTEGER NOT NULL,
            ramp_up INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            metrics TEXT NOT NULL,
            cost_monthly REAL NOT NULL,
            score REAL NOT NULL,
            timestamp TEXT NOT NULL,
            output_path TEXT,
            FOREIGN KEY (test_id) REFERENCES tests(id)
        )
    """)
    
    conn.commit()
    conn.close()


def test_to_response(row: dict, include_counts: bool = True) -> TestResponse:
    resource_config = None
    replica_config = None
    traffic_config = None
    jmx_config = None
    
    if row.get("resource_config"):
        try:
            resource_config = ResourceConfig(**json.loads(row["resource_config"]))
        except:
            resource_config = None
    
    if row.get("replica_config"):
        try:
            replica_config = ReplicaConfig(**json.loads(row["replica_config"]))
        except:
            replica_config = None
    
    if row.get("traffic_config"):
        try:
            traffic_config = TrafficConfig(**json.loads(row["traffic_config"]))
        except:
            traffic_config = None
    
    if row.get("jmx_config"):
        try:
            jmx_config_dict = json.loads(row["jmx_config"])
            jmx_config = JmxTestCreate(**jmx_config_dict)
        except:
            jmx_config = None
    
    return TestResponse(
        id=row["id"],
        name=row["name"],
        test_type=row.get("test_type", "matrix"),
        cloud_provider=row["cloud_provider"],
        region=row["region"],
        resource_config=resource_config,
        replica_config=replica_config,
        traffic_config=traffic_config,
        jmx_config=jmx_config,
        status=row["status"],
        created_at=row["created_at"],
        completed_at=row["completed_at"],
        total_configs=row.get("total_configs", 0),
        results_count=row.get("results_count", 0)
    )


def result_to_response(row: dict) -> ResultResponse:
    return ResultResponse(
        id=row["id"],
        test_id=row["test_id"],
        config=ConfigSpec(**json.loads(row["config"])),
        metrics=Metrics(**json.loads(row["metrics"])),
        cost_monthly=row["cost_monthly"],
        score=row["score"],
        timestamp=row["timestamp"]
    )


def jmx_result_to_response(row: dict) -> JmxResultResponse:
    return JmxResultResponse(
        id=row["id"],
        test_id=row["test_id"],
        jmx_filename=row["jmx_filename"],
        threads=row["threads"],
        ramp_up=row["ramp_up"],
        duration=row["duration"],
        metrics=JmxMetrics(**json.loads(row["metrics"])),
        cost_monthly=row["cost_monthly"],
        score=row["score"],
        timestamp=row["timestamp"],
        output_path=row.get("output_path")
    )


@app.get("/")
async def root():
    return {"message": "LoadPilot API", "version": "1.0.0"}


@app.get("/api/dashboard", response_model=TestListResponse)
async def get_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM tests")
    total_tests = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM tests WHERE status = 'completed'")
    completed_tests = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM tests WHERE status = 'running'")
    active_tests = cursor.fetchone()["count"]
    
    cursor.execute("SELECT SUM(results_count) as total FROM tests")
    total_configs = cursor.fetchone()["total"] or 0
    
    cursor.execute("""
        SELECT * FROM tests 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    rows = cursor.fetchall()
    conn.close()
    
    stats = DashboardStats(
        total_tests=total_tests,
        completed_tests=completed_tests,
        active_tests=active_tests,
        avg_cost_savings=0.0,
        total_configs_tested=total_configs
    )
    
    tests = [test_to_response(dict(row)) for row in rows]
    
    return TestListResponse(tests=tests, stats=stats)


@app.post("/api/tests", response_model=TestResponse)
async def create_test(test: TestCreate):
    test_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    resource_config = test.resource_config.model_dump()
    replica_config = test.replica_config.model_dump()
    traffic_config = test.traffic_config.model_dump()
    
    configs = generate_config_matrix(test.resource_config, test.replica_config)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tests (id, name, test_type, cloud_provider, region, 
                          resource_config, replica_config, traffic_config,
                          status, created_at, total_configs)
        VALUES (?, ?, 'matrix', ?, ?, ?, ?, ?, 'pending', ?, ?)
    """, (
        test_id, test.name, test.cloud_provider, test.region,
        json.dumps(resource_config), json.dumps(replica_config), 
        json.dumps(traffic_config), now, len(configs)
    ))
    
    conn.commit()
    conn.close()
    
    row = {
        "id": test_id,
        "name": test.name,
        "test_type": "matrix",
        "cloud_provider": test.cloud_provider,
        "region": test.region,
        "resource_config": json.dumps(resource_config),
        "replica_config": json.dumps(replica_config),
        "traffic_config": json.dumps(traffic_config),
        "jmx_config": None,
        "status": "pending",
        "created_at": now,
        "completed_at": None,
        "total_configs": len(configs),
        "results_count": 0
    }
    
    return test_to_response(row)


@app.post("/api/tests/jmx", response_model=TestResponse)
async def create_jmx_test(
    name: str,
    cloud_provider: str = "aws",
    region: str = "us-east-1",
    threads: int = 100,
    ramp_up: int = 60,
    duration: int = 300,
    jmx_file: UploadFile = File(...)
):
    if not jmx_file.filename or not jmx_file.filename.endswith('.jmx'):
        raise HTTPException(status_code=400, detail="File must be a .jmx file")
    
    test_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    safe_filename = jmx_file.filename.replace(" ", "_")
    jmx_filename = f"{test_id}_{safe_filename}"
    jmx_path = os.path.join(UPLOAD_DIR, jmx_filename)
    
    with open(jmx_path, "wb") as f:
        content = await jmx_file.read()
        f.write(content)
    
    jmx_config = {
        "name": name,
        "cloud_provider": cloud_provider,
        "region": region,
        "threads": threads,
        "ramp_up": ramp_up,
        "duration": duration
    }
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tests (id, name, test_type, cloud_provider, region, 
                          jmx_config, jmx_filename, status, created_at)
        VALUES (?, ?, 'jmx', ?, ?, ?, ?, 'pending', ?)
    """, (
        test_id, name, cloud_provider, region,
        json.dumps(jmx_config), jmx_filename, now
    ))
    
    conn.commit()
    conn.close()
    
    row = {
        "id": test_id,
        "name": name,
        "test_type": "jmx",
        "cloud_provider": cloud_provider,
        "region": region,
        "resource_config": None,
        "replica_config": None,
        "traffic_config": None,
        "jmx_config": json.dumps(jmx_config),
        "status": "pending",
        "created_at": now,
        "completed_at": None,
        "total_configs": 1,
        "results_count": 0
    }
    
    return test_to_response(row)


@app.get("/api/tests", response_model=List[TestResponse])
async def list_tests():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM tests 
        ORDER BY created_at DESC 
        LIMIT 50
    """)
    rows = cursor.fetchall()
    conn.close()
    
    return [test_to_response(dict(row)) for row in rows]


@app.get("/api/tests/{test_id}", response_model=TestDetailResponse)
async def get_test(test_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tests WHERE id = ?", (test_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")
    
    row = dict(row)
    
    cursor.execute("SELECT * FROM results WHERE test_id = ?", (test_id,))
    result_rows = cursor.fetchall()
    
    cursor.execute("SELECT * FROM jmx_results WHERE test_id = ?", (test_id,))
    jmx_result_rows = cursor.fetchall()
    
    conn.close()
    
    results = [result_to_response(dict(r)) for r in result_rows]
    jmx_results = [jmx_result_to_response(dict(r)) for r in jmx_result_rows]
    
    winner = find_winner([r.model_dump() for r in results]) if results else None
    
    if winner:
        winner_response = ResultResponse(
            id=winner["id"],
            test_id=winner["test_id"],
            config=ConfigSpec(**winner["config"]),
            metrics=Metrics(**winner["metrics"]),
            cost_monthly=winner["cost_monthly"],
            score=winner["score"],
            timestamp=winner["timestamp"]
        )
    else:
        winner_response = None
    
    return TestDetailResponse(
        **test_to_response(row).model_dump(),
        results=results,
        jmx_results=jmx_results,
        winner=winner_response
    )


@app.post("/api/tests/{test_id}/run")
async def run_test(test_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tests WHERE id = ?", (test_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")
    
    if row["status"] == "running":
        conn.close()
        raise HTTPException(status_code=400, detail="Test already running")
    
    test_dict = dict(row)
    
    if test_dict.get("test_type") == "jmx":
        conn.close()
        return await run_jmx_test(test_id)
    
    resource_config = ResourceConfig(**json.loads(test_dict["resource_config"]))
    replica_config = ReplicaConfig(**json.loads(test_dict["replica_config"]))
    traffic_config = TrafficConfig(**json.loads(test_dict["traffic_config"]))
    
    cursor.execute("UPDATE tests SET status = 'running' WHERE id = ?", (test_id,))
    conn.commit()
    
    configs = generate_config_matrix(resource_config, replica_config)
    
    baseline_cost = None
    results = []
    
    for config in configs:
        cost = calculate_monthly_cost(
            config.cpu, config.memory, config.replicas,
            test_dict["cloud_provider"], test_dict["region"]
        )
        
        if baseline_cost is None:
            baseline_cost = cost
        
        metrics = simulate_metrics(config.cpu, config.memory, 
                                 config.replicas, traffic_config)
        score = calculate_score(metrics, cost, baseline_cost)
        
        result_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO results (id, test_id, config, metrics, cost_monthly, score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            result_id, test_id, 
            json.dumps(config.model_dump()),
            json.dumps(metrics.model_dump()),
            cost, score, now
        ))
        
        results.append({
            "id": result_id,
            "test_id": test_id,
            "config": config.model_dump(),
            "metrics": metrics.model_dump(),
            "cost_monthly": cost,
            "score": score,
            "timestamp": now
        })
    
    cursor.execute("""
        UPDATE tests 
        SET status = 'completed', 
            completed_at = ?,
            results_count = ?
        WHERE id = ?
    """, (datetime.utcnow().isoformat(), len(results), test_id))
    
    conn.commit()
    conn.close()
    
    return {"message": "Test completed", "results_count": len(results)}


@app.post("/api/tests/{test_id}/run-jmx")
async def run_jmx_test(test_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tests WHERE id = ?", (test_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")
    
    row = dict(row)
    
    if row.get("test_type") != "jmx":
        conn.close()
        raise HTTPException(status_code=400, detail="Not a JMX test")
    
    if row["status"] == "running":
        conn.close()
        raise HTTPException(status_code=400, detail="Test already running")
    
    jmx_config = json.loads(row["jmx_config"])
    jmx_filename = row["jmx_filename"]
    jmx_path = os.path.join(UPLOAD_DIR, jmx_filename)
    
    if not os.path.exists(jmx_path):
        conn.close()
        raise HTTPException(status_code=400, detail="JMX file not found")
    
    jmeter_path = shutil.which("jmeter") or "/opt/apache-jmeter/bin/jmeter"
    
    if not os.path.exists(jmeter_path):
        conn.close()
        raise HTTPException(status_code=400, detail="JMeter not installed. Please install JMeter to run JMX tests.")
    
    cursor.execute("UPDATE tests SET status = 'running' WHERE id = ?", (test_id,))
    conn.commit()
    conn.close()
    
    run_id = str(uuid.uuid4())
    output_dir = os.path.join(JMX_RESULTS_DIR, run_id)
    os.makedirs(output_dir, exist_ok=True)
    
    csv_file = os.path.join(output_dir, "results.csv")
    
    try:
        cmd = [
            jmeter_path,
            "-n",
            "-t", jmx_path,
            "-l", csv_file,
            "-e",
            "-o", output_dir,
            "-Jthreads", str(jmx_config["threads"]),
            "-Jrampup", str(jmx_config["ramp_up"]),
            "-Jduration", str(jmx_config["duration"])
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=jmx_config["duration"] + 120
        )
        
        if result.returncode != 0:
            raise Exception(f"JMeter failed: {result.stderr}")
        
        metrics = parse_jmeter_results(csv_file, jmx_config["threads"])
        
        cost = calculate_monthly_cost(
            1000, 2048, 1,
            jmx_config["cloud_provider"],
            jmx_config["region"]
        )
        
        baseline_cost = cost
        score = calculate_score(
            Metrics(
                latency_p50=metrics.latency_p50,
                latency_p95=metrics.latency_p95,
                latency_p99=metrics.latency_p99,
                throughput=metrics.throughput,
                error_rate=metrics.error_rate
            ),
            cost,
            baseline_cost
        )
        
        result_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO jmx_results (id, test_id, jmx_filename, threads, ramp_up, duration,
                                    metrics, cost_monthly, score, timestamp, output_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result_id, test_id, jmx_filename, jmx_config["threads"],
            jmx_config["ramp_up"], jmx_config["duration"],
            json.dumps(metrics.model_dump()), cost, score, now, output_dir
        ))
        
        cursor.execute("""
            UPDATE tests 
            SET status = 'completed', completed_at = ?, results_count = 1
            WHERE id = ?
        """, (now, test_id))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "JMX test completed",
            "result_id": result_id,
            "metrics": metrics.model_dump(),
            "score": score,
            "output_path": output_dir
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="JMeter test timed out")
    except Exception as e:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE tests SET status = 'failed' WHERE id = ?", (test_id,))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=500, detail=f"JMX test failed: {str(e)}")


def parse_jmeter_results(csv_path: str, threads: int) -> JmxMetrics:
    latencies = []
    response_times = []
    total_requests = 0
    failed_requests = 0
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    elapsed = float(row.get('elapsed', 0) or 0)
                    latency = float(row.get('Latency', 0) or 0)
                    success = row.get('success', 'true').lower() == 'true'
                    
                    if elapsed > 0:
                        response_times.append(elapsed)
                    if latency > 0:
                        latencies.append(latency)
                    
                    total_requests += 1
                    if not success:
                        failed_requests += 1
                except (ValueError, KeyError):
                    continue
        
        if not response_times:
            response_times = [100.0]
        if not latencies:
            latencies = [50.0]
        
        response_times.sort()
        latencies.sort()
        
        n = len(response_times)
        p50_idx = int(n * 0.50)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)
        
        duration = 300
        throughput = total_requests / duration if duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        return JmxMetrics(
            latency_p50=round(latencies[p50_idx], 2),
            latency_p95=round(latencies[p95_idx], 2),
            latency_p99=round(latencies[p99_idx], 2),
            latency_avg=round(sum(latencies) / len(latencies), 2),
            throughput=round(throughput, 2),
            error_rate=round(error_rate, 2),
            total_requests=total_requests,
            failed_requests=failed_requests
        )
        
    except Exception as e:
        return JmxMetrics(
            latency_p50=100.0,
            latency_p95=300.0,
            latency_p99=500.0,
            latency_avg=150.0,
            throughput=100.0,
            error_rate=0.0,
            total_requests=0,
            failed_requests=0
        )


@app.delete("/api/tests/{test_id}")
async def delete_test(test_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, jmx_filename FROM tests WHERE id = ?", (test_id,))
    test = cursor.fetchone()
    
    if not test:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test["jmx_filename"]:
        jmx_path = os.path.join(UPLOAD_DIR, test["jmx_filename"])
        if os.path.exists(jmx_path):
            os.remove(jmx_path)
    
    cursor.execute("DELETE FROM results WHERE test_id = ?", (test_id,))
    cursor.execute("DELETE FROM jmx_results WHERE test_id = ?", (test_id,))
    cursor.execute("DELETE FROM tests WHERE id = ?", (test_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Test deleted"}


@app.get("/api/jmeter/check")
async def check_jmeter():
    jmeter_path = shutil.which("jmeter") or "/opt/apache-jmeter/bin/jmeter"
    installed = os.path.exists(jmeter_path)
    
    return {
        "installed": installed,
        "path": jmeter_path if installed else None,
        "message": "JMeter is installed" if installed else "JMeter not found. Install from https://jmeter.apache.org/"
    }


# MVP2: Ollama AI Integration

from ollama_client import OllamaClient, LoadTestAdvisor, parse_config_from_ai_response

ollama_client = OllamaClient()
load_advisor = LoadTestAdvisor(ollama_client)


@app.get("/api/ai/check")
async def check_ollama():
    """Check if Ollama is available."""
    health = ollama_client.check_health()
    return health


@app.get("/api/ai/models")
async def get_ollama_models():
    """Get list of available Ollama models."""
    models = ollama_client.list_models()
    return {
        "available": ollama_client.is_available(),
        "models": models,
        "current_model": ollama_client.model
    }


@app.post("/api/ai/model")
async def set_ollama_model(model: str):
    """Set the active Ollama model."""
    available_models = ollama_client.list_models()
    if model not in available_models:
        raise HTTPException(status_code=400, detail=f"Model '{model}' not available")
    ollama_client.set_model(model)
    return {"model": model, "message": "Model set successfully"}


@app.post("/api/ai/recommend/{test_id}")
async def get_ai_recommendation(test_id: str):
    """Get AI-powered recommendations for a test."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tests WHERE id = ?", (test_id,))
    test = cursor.fetchone()
    
    if not test:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")
    
    cursor.execute("SELECT * FROM results WHERE test_id = ?", (test_id,))
    results = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM jmx_results WHERE test_id = ?", (test_id,))
    jmx_results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    if not results and not jmx_results:
        return {"recommendation": "No test results yet. Run a test first."}
    
    all_results = []
    
    for r in results:
        all_results.append({
            "config": json.loads(r["config"]),
            "metrics": json.loads(r["metrics"]),
            "cost_monthly": r["cost_monthly"],
            "score": r["score"]
        })
    
    for r in jmx_results:
        all_results.append({
            "metrics": json.loads(r["metrics"]),
            "cost_monthly": r["cost_monthly"],
            "score": r["score"]
        })
    
    recommendation = load_advisor.compare_configs(all_results)
    
    return {
        "test_id": test_id,
        "results_count": len(all_results),
        "recommendation": recommendation
    }


@app.post("/api/ai/summary/{test_id}")
async def get_ai_summary(test_id: str):
    """Get AI summary of test results."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM tests WHERE id = ?", (test_id,))
    test = cursor.fetchone()
    
    if not test:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")
    
    cursor.execute("SELECT * FROM results WHERE test_id = ?", (test_id,))
    results = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM jmx_results WHERE test_id = ?", (test_id,))
    jmx_results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    formatted_results = []
    
    for r in results:
        formatted_results.append({
            "config": json.loads(r["config"]),
            "metrics": json.loads(r["metrics"]),
            "cost_monthly": r["cost_monthly"],
            "score": r["score"]
        })
    
    for r in jmx_results:
        formatted_results.append({
            "metrics": json.loads(r["metrics"]),
            "cost_monthly": r["cost_monthly"],
            "score": r["score"]
        })
    
    summary = load_advisor.generate_summary(test["name"], formatted_results)
    
    return {
        "test_id": test_id,
        "test_name": test["name"],
        "summary": summary
    }


# MVP2: Test Control (Stop/Start/Scale)

from test_runner import LoadTestRunner, LoadTestConfig, TestStatus

test_runner = LoadTestRunner(output_base_dir="test_runs")


@app.post("/api/load-test/start")
async def start_load_test(
    name: str,
    threads: int = 100,
    ramp_up: int = 60,
    duration: int = 300,
    jmx_file: UploadFile = File(...)
):
    """Start an interactive load test with real-time control."""
    if not jmx_file.filename or not jmx_file.filename.endswith('.jmx'):
        raise HTTPException(status_code=400, detail="File must be a .jmx file")
    
    test_id = str(uuid.uuid4())
    jmx_filename = f"{test_id}_{jmx_file.filename.replace(' ', '_')}"
    jmx_path = os.path.join(UPLOAD_DIR, jmx_filename)
    
    with open(jmx_path, "wb") as f:
        f.write(await jmx_file.read())
    
    config = LoadTestConfig(
        jmx_path=jmx_path,
        threads=threads,
        ramp_up=ramp_up,
        duration=duration
    )
    
    created_test_id = test_runner.create_test(config)
    test_runner.start(created_test_id, config)
    
    return {
        "test_id": created_test_id,
        "status": "running",
        "threads": threads,
        "duration": duration,
        "message": "Load test started. Use /api/load-test/{test_id}/status to monitor."
    }


@app.get("/api/load-test/{test_id}/status")
async def get_load_test_status(test_id: str):
    """Get current status of a load test."""
    status = test_runner.get_status(test_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return status


@app.post("/api/load-test/{test_id}/stop")
async def stop_load_test(test_id: str):
    """Stop a running load test."""
    success = test_runner.stop(test_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop test")
    
    return {"test_id": test_id, "status": "stopped"}


@app.post("/api/load-test/{test_id}/pause")
async def pause_load_test(test_id: str):
    """Pause a running load test."""
    success = test_runner.pause(test_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to pause test")
    
    return {"test_id": test_id, "status": "paused"}


@app.post("/api/load-test/{test_id}/resume")
async def resume_load_test(test_id: str):
    """Resume a paused load test."""
    success = test_runner.resume(test_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to resume test")
    
    return {"test_id": test_id, "status": "running"}


@app.post("/api/load-test/{test_id}/scale")
async def scale_load_test(test_id: str, threads: int):
    """Scale load test to specific thread count."""
    success = test_runner.scale(test_id, threads)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to scale test")
    
    return {"test_id": test_id, "threads": threads, "status": "scaled"}


@app.post("/api/load-test/{test_id}/increase")
async def increase_load(test_id: str, percent: int = 25):
    """Increase load by percentage."""
    success = test_runner.increase_load(test_id, percent)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to increase load")
    
    status = test_runner.get_status(test_id)
    return {
        "test_id": test_id,
        "increase_percent": percent,
        "new_threads": status["target_threads"] if status else 0,
        "status": "increased"
    }


@app.post("/api/load-test/{test_id}/decrease")
async def decrease_load(test_id: str, percent: int = 25):
    """Decrease load by percentage."""
    success = test_runner.decrease_load(test_id, percent)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to decrease load")
    
    status = test_runner.get_status(test_id)
    return {
        "test_id": test_id,
        "decrease_percent": percent,
        "new_threads": status["target_threads"] if status else 0,
        "status": "decreased"
    }


@app.get("/api/load-test/{test_id}/results")
async def get_load_test_results(test_id: str):
    """Get all results from a load test."""
    results = test_runner.get_results(test_id)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return {"test_id": test_id, "results": results}


@app.post("/api/load-test/{test_id}/ai-decide")
async def ai_decision(test_id: str):
    """Get AI recommendation for next action."""
    status = test_runner.get_status(test_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if status["current_metrics"]:
        recommendation = load_advisor.analyze_results({
            "config": {"threads": status["target_threads"]},
            "metrics": status["current_metrics"],
            "cost_monthly": 0,
            "score": 0
        })
    else:
        recommendation = "Not enough data yet. Continue monitoring."
    
    return {
        "test_id": test_id,
        "current_status": status,
        "ai_recommendation": recommendation
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Kubernetes Integration Endpoints

from k8s_client import kubernetes_client, PodConfig, ClusterStatus

k8s_deployments = {}


@app.get("/api/k8s/status")
async def get_k8s_status():
    """Get Kubernetes cluster connection status."""
    return {
        "status": kubernetes_client.status.value,
        "cluster_info": kubernetes_client.cluster_info
    }


@app.post("/api/k8s/connect")
async def connect_k8s(kubeconfig_path: Optional[str] = None, namespace: str = "default"):
    """Connect to Kubernetes cluster."""
    result = kubernetes_client.check_connection(kubeconfig_path)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error", "Connection failed"))
    
    return {
        "message": "Connected successfully",
        "cluster_info": result,
        "namespaces": kubernetes_client.get_namespaces()
    }


@app.post("/api/k8s/disconnect")
async def disconnect_k8s():
    """Disconnect from Kubernetes cluster."""
    kubernetes_client.disconnect()
    return {"message": "Disconnected"}


@app.get("/api/k8s/namespaces")
async def get_k8s_namespaces():
    """Get list of namespaces."""
    namespaces = kubernetes_client.get_namespaces()
    return {"namespaces": namespaces}


@app.post("/api/k8s/deploy")
async def deploy_k8s_test(
    name: str,
    cpu_millicores: int = 500,
    memory_mb: int = 512,
    replicas: int = 1,
    image: str = "nginx",
    namespace: str = "default"
):
    """Deploy test pods to Kubernetes cluster."""
    if kubernetes_client.status != ClusterStatus.CONNECTED:
        raise HTTPException(status_code=400, detail="Not connected to cluster")
    
    config = PodConfig(
        name=name,
        cpu_millicores=cpu_millicores,
        memory_mb=memory_mb,
        image=image,
        replicas=replicas
    )
    
    result = kubernetes_client.deploy_test_pods(config, namespace)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    deployment_id = str(uuid.uuid4())
    k8s_deployments[deployment_id] = {
        "id": deployment_id,
        "name": name,
        "deployment": result["deployment"],
        "service": result["service"],
        "namespace": namespace,
        "config": config.__dict__,
        "status": "deployed",
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "deployment_id": deployment_id,
        "details": result,
        "message": "Test pods deployed successfully"
    }


@app.get("/api/k8s/deployments")
async def list_k8s_deployments():
    """List all LoadPilot deployments."""
    return {"deployments": list(k8s_deployments.values())}


@app.get("/api/k8s/deployments/{deployment_id}")
async def get_k8s_deployment(deployment_id: str):
    """Get details of a specific deployment."""
    if deployment_id not in k8s_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    dep = k8s_deployments[deployment_id]
    metrics = kubernetes_client.get_pod_metrics(dep["namespace"])
    
    return {
        "deployment": dep,
        "metrics": metrics
    }


@app.delete("/api/k8s/deployments/{deployment_id}")
async def delete_k8s_deployment(deployment_id: str):
    """Delete a LoadPilot deployment."""
    if deployment_id not in k8s_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    dep = k8s_deployments[deployment_id]
    success = kubernetes_client.delete_test_resources(
        dep["deployment"],
        dep["service"],
        dep["namespace"]
    )
    
    if success:
        del k8s_deployments[deployment_id]
        return {"message": "Deployment deleted"}
    
    raise HTTPException(status_code=500, detail="Failed to delete deployment")


@app.post("/api/k8s/deployments/{deployment_id}/scale")
async def scale_k8s_deployment(deployment_id: str, replicas: int):
    """Scale a deployment."""
    if deployment_id not in k8s_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    dep = k8s_deployments[deployment_id]
    success = kubernetes_client.scale_deployment(
        dep["deployment"],
        replicas,
        dep["namespace"]
    )
    
    if success:
        dep["config"]["replicas"] = replicas
        return {"message": f"Scaled to {replicas} replicas"}
    
    raise HTTPException(status_code=500, detail="Failed to scale deployment")


@app.get("/api/k8s/metrics")
async def get_k8s_metrics(namespace: str = "default"):
    """Get cluster metrics."""
    if kubernetes_client.status != ClusterStatus.CONNECTED:
        raise HTTPException(status_code=400, detail="Not connected to cluster")
    
    return kubernetes_client.get_pod_metrics(namespace)


@app.post("/api/k8s/run-test")
async def run_k8s_load_test(
    name: str,
    cpu_millicores: int = 500,
    memory_mb: int = 512,
    replicas: int = 1,
    threads: int = 100,
    duration: int = 60,
    namespace: str = "default",
    jmx_file: UploadFile = File(None)
):
    """Run a load test on Kubernetes cluster with specific config."""
    if kubernetes_client.status != ClusterStatus.CONNECTED:
        raise HTTPException(status_code=400, detail="Not connected to cluster")
    
    config = PodConfig(
        name=f"{name}-{uuid.uuid4().hex[:8]}",
        cpu_millicores=cpu_millicores,
        memory_mb=memory_mb,
        image="nginx",
        replicas=replicas
    )
    
    deploy_result = kubernetes_client.deploy_test_pods(config, namespace)
    
    if deploy_result.get("status") == "error":
        raise HTTPException(status_code=500, detail=deploy_result.get("error"))
    
    test_id = str(uuid.uuid4())
    
    cost = calculate_monthly_cost(
        cpu_millicores, memory_mb, replicas, "aws", "us-east-1"
    )
    
    k8s_deployments[test_id] = {
        "id": test_id,
        "name": name,
        "deployment": deploy_result["deployment"],
        "service": deploy_result["service"],
        "namespace": namespace,
        "config": config.__dict__,
        "pod_ips": deploy_result.get("pod_ips", []),
        "status": "testing",
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "test_id": test_id,
        "deployment": deploy_result,
        "cost_monthly": cost,
        "message": "Test pods deployed. Run load test against pod IPs."
    }
