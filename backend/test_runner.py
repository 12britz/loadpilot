"""
Load test runner with stop/start/scale capabilities.
"""

import os
import json
import uuid
import subprocess
import threading
import time
import csv
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from models import JmxMetrics
from cost_calculator import calculate_monthly_cost


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class TestPhase(Enum):
    RAMP_UP = "ramp_up"
    SUSTAINED = "sustained"
    RAMP_DOWN = "ramp_down"
    COMPLETE = "complete"


@dataclass
class LoadTestConfig:
    jmx_path: str
    threads: int = 100
    ramp_up: int = 60
    duration: int = 300
    target_rps: Optional[int] = None
    cloud_provider: str = "aws"
    region: str = "us-east-1"
    output_dir: str = "test_runs"


@dataclass
class LoadTestState:
    test_id: str
    status: TestStatus = TestStatus.PENDING
    phase: TestPhase = TestPhase.RAMP_UP
    current_threads: int = 0
    target_threads: int = 100
    elapsed_seconds: int = 0
    total_seconds: int = 300
    progress_percent: float = 0.0
    current_metrics: Optional[Dict] = None
    results: List[Dict] = field(default_factory=list)
    start_time: Optional[datetime] = None
    process: Optional[Any] = None
    csv_output: Optional[str] = None
    should_stop: bool = False
    should_pause: bool = False


class LoadTestRunner:
    """
    Orchestrates load tests with support for:
    - Start/Stop
    - Pause/Resume  
    - Dynamic scaling (increase/decrease threads)
    - Real-time metrics
    - AI-powered recommendations
    """
    
    def __init__(self, output_base_dir: str = "test_runs"):
        self.output_base_dir = output_base_dir
        self.active_tests: Dict[str, LoadTestState] = {}
        self._lock = threading.Lock()
        os.makedirs(output_base_dir, exist_ok=True)
    
    def create_test(self, config: LoadTestConfig) -> str:
        """Create a new load test and return its ID."""
        test_id = str(uuid.uuid4())
        
        output_dir = os.path.join(self.output_base_dir, test_id)
        os.makedirs(output_dir, exist_ok=True)
        
        state = LoadTestState(
            test_id=test_id,
            target_threads=config.threads,
            total_seconds=config.duration
        )
        
        with self._lock:
            self.active_tests[test_id] = state
        
        return test_id
    
    def start(self, test_id: str, config: LoadTestConfig) -> bool:
        """Start or resume a load test."""
        with self._lock:
            if test_id not in self.active_tests:
                return False
            
            state = self.active_tests[test_id]
            
            if state.status == TestStatus.RUNNING:
                return False
            
            if state.status == TestStatus.COMPLETED:
                return False
            
            state.status = TestStatus.RUNNING
            state.start_time = datetime.utcnow()
            state.should_stop = False
            state.should_pause = False
        
        thread = threading.Thread(target=self._run_test, args=(test_id, config))
        thread.daemon = True
        thread.start()
        
        return True
    
    def stop(self, test_id: str) -> bool:
        """Stop a running test."""
        with self._lock:
            if test_id not in self.active_tests:
                return False
            
            state = self.active_tests[test_id]
            state.should_stop = True
            state.status = TestStatus.STOPPED
            
            if state.process:
                try:
                    state.process.terminate()
                except:
                    pass
        
        return True
    
    def pause(self, test_id: str) -> bool:
        """Pause a running test (reduces threads to 0)."""
        with self._lock:
            if test_id not in self.active_tests:
                return False
            
            state = self.active_tests[test_id]
            
            if state.status != TestStatus.RUNNING:
                return False
            
            state.should_pause = True
            state.status = TestStatus.PAUSED
        
        return True
    
    def resume(self, test_id: str) -> bool:
        """Resume a paused test."""
        with self._lock:
            if test_id not in self.active_tests:
                return False
            
            state = self.active_tests[test_id]
            
            if state.status != TestStatus.PAUSED:
                return False
            
            state.status = TestStatus.RUNNING
            state.should_pause = False
        
        return True
    
    def scale(self, test_id: str, threads: int) -> bool:
        """Dynamically scale threads up or down during a test."""
        with self._lock:
            if test_id not in self.active_tests:
                return False
            
            state = self.active_tests[test_id]
            
            if state.status != TestStatus.RUNNING:
                return False
            
            state.target_threads = max(1, min(threads, 10000))
        
        return True
    
    def increase_load(self, test_id: str, percent: int = 25) -> bool:
        """Increase load by a percentage."""
        with self._lock:
            if test_id not in self.active_tests:
                return False
            
            state = self.active_tests[test_id]
            new_threads = int(state.target_threads * (1 + percent / 100))
            state.target_threads = min(new_threads, 10000)
        
        return True
    
    def decrease_load(self, test_id: str, percent: int = 25) -> bool:
        """Decrease load by a percentage."""
        with self._lock:
            if test_id not in self.active_tests:
                return False
            
            state = self.active_tests[test_id]
            new_threads = int(state.target_threads * (1 - percent / 100))
            state.target_threads = max(new_threads, 1)
        
        return True
    
    def get_status(self, test_id: str) -> Optional[Dict]:
        """Get current test status."""
        with self._lock:
            if test_id not in self.active_tests:
                return None
            
            state = self.active_tests[test_id]
            
            return {
                "test_id": state.test_id,
                "status": state.status.value,
                "phase": state.phase.value,
                "current_threads": state.current_threads,
                "target_threads": state.target_threads,
                "elapsed_seconds": state.elapsed_seconds,
                "total_seconds": state.total_seconds,
                "progress_percent": state.progress_percent,
                "current_metrics": state.current_metrics,
                "results_count": len(state.results)
            }
    
    def get_results(self, test_id: str) -> Optional[List[Dict]]:
        """Get test results."""
        with self._lock:
            if test_id not in self.active_tests:
                return None
            
            return self.active_tests[test_id].results.copy()
    
    def _run_test(self, test_id: str, config: LoadTestConfig):
        """Internal method to run the test."""
        state = self.active_tests[test_id]
        csv_path = os.path.join(self.output_base_dir, test_id, "results.csv")
        state.csv_output = csv_path
        
        jmeter_path = self._find_jmeter()
        
        if not jmeter_path:
            state.status = TestStatus.FAILED
            return
        
        cmd = [
            jmeter_path,
            "-n",
            "-t", config.jmx_path,
            "-l", csv_path,
            "-e",
            "-o", os.path.join(self.output_base_dir, test_id, "html"),
            "-Jthreads", str(state.target_threads),
            "-Jrampup", str(config.ramp_up),
            "-Jduration", str(config.duration)
        ]
        
        try:
            state.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            start_time = time.time()
            
            while state.process.poll() is None:
                if state.should_stop:
                    state.process.terminate()
                    break
                
                if state.should_pause:
                    time.sleep(1)
                    continue
                
                elapsed = int(time.time() - start_time)
                
                with self._lock:
                    state.elapsed_seconds = elapsed
                    state.progress_percent = min(100, (elapsed / config.duration) * 100)
                    state.current_threads = state.target_threads
                    
                    if elapsed < config.ramp_up:
                        state.phase = TestPhase.RAMP_UP
                        state.current_threads = int(state.target_threads * (elapsed / config.ramp_up))
                    elif elapsed < config.duration - config.ramp_up * 0.5:
                        state.phase = TestPhase.SUSTAINED
                    else:
                        state.phase = TestPhase.RAMP_DOWN
                        state.current_threads = int(state.target_threads * ((config.duration - elapsed) / (config.ramp_up * 0.5)))
                
                metrics = self._parse_partial_results(csv_path)
                if metrics:
                    with self._lock:
                        state.current_metrics = metrics
                
                time.sleep(2)
            
            if not state.should_stop:
                state.status = TestStatus.COMPLETED
                state.progress_percent = 100
                
                final_metrics = self._parse_final_results(csv_path, state.target_threads)
                if final_metrics:
                    with self._lock:
                        state.current_metrics = final_metrics
                        state.results.append({
                            "threads": state.target_threads,
                            "metrics": final_metrics,
                            "timestamp": datetime.utcnow().isoformat()
                        })
            else:
                state.status = TestStatus.STOPPED
            
        except Exception as e:
            state.status = TestStatus.FAILED
        
        finally:
            with self._lock:
                state.process = None
    
    def _find_jmeter(self) -> Optional[str]:
        """Find JMeter executable."""
        paths = [
            shutil.which("jmeter"),
            "/opt/apache-jmeter/bin/jmeter",
            "/usr/share/jmeter/bin/jmeter",
            "/usr/local/apache-jmeter/bin/jmeter",
            "C:/Program Files/apache-jmeter/bin/jmeter.exe"
        ]
        
        for path in paths:
            if path and os.path.exists(path):
                return path
        
        return None
    
    def _parse_partial_results(self, csv_path: str) -> Optional[Dict]:
        """Parse partial results during test execution."""
        if not os.path.exists(csv_path):
            return None
        
        try:
            latencies = []
            response_times = []
            total = 0
            failed = 0
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        elapsed = float(row.get('elapsed', 0) or 0)
                        latency = float(row.get('Latency', 0) or 0)
                        
                        if elapsed > 0:
                            response_times.append(elapsed)
                        if latency > 0:
                            latencies.append(latency)
                        
                        total += 1
                        if row.get('success', 'true').lower() != 'true':
                            failed += 1
                    except:
                        continue
            
            if not response_times:
                return None
            
            response_times.sort()
            latencies.sort()
            n = len(response_times)
            
            duration = 300
            throughput = total / duration if duration > 0 else 0
            error_rate = (failed / total * 100) if total > 0 else 0
            
            return {
                "latency_p50": round(latencies[int(n * 0.50)], 2),
                "latency_p95": round(latencies[int(n * 0.95)], 2),
                "latency_p99": round(latencies[int(n * 0.99)], 2),
                "latency_avg": round(sum(latencies) / len(latencies), 2),
                "throughput": round(throughput, 2),
                "error_rate": round(error_rate, 2),
                "total_requests": total,
                "failed_requests": failed
            }
        except:
            return None
    
    def _parse_final_results(self, csv_path: str, threads: int) -> Optional[Dict]:
        """Parse final results after test completion."""
        return self._parse_partial_results(csv_path)


import shutil
