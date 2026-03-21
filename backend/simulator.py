"""
Simulates load test results for pod configurations.
"""

import random
import math
from typing import List, Dict, Optional
from models import ConfigSpec, Metrics, ResourceConfig, ReplicaConfig, TrafficConfig


def generate_config_matrix(resource_config: ResourceConfig, 
                          replica_config: ReplicaConfig) -> List[ConfigSpec]:
    """Generate all config combinations to test."""
    configs = []
    
    cpu_values = list(range(
        resource_config.cpu_min, 
        resource_config.cpu_max + 1, 
        resource_config.cpu_step
    ))
    if resource_config.cpu_max not in cpu_values:
        cpu_values.append(resource_config.cpu_max)
    
    memory_values = list(range(
        resource_config.memory_min,
        resource_config.memory_max + 1,
        resource_config.memory_step
    ))
    if resource_config.memory_max not in memory_values:
        memory_values.append(resource_config.memory_max)
    
    replica_values = list(range(
        replica_config.min,
        replica_config.max + 1
    ))
    if replica_config.max not in replica_values:
        replica_values.append(replica_config.max)
    
    for cpu in cpu_values:
        for memory in memory_values:
            for replicas in replica_values:
                configs.append(ConfigSpec(cpu=cpu, memory=memory, replicas=replicas))
    
    return configs


def simulate_metrics(cpu: int, memory: int, replicas: int, 
                     traffic: TrafficConfig) -> Metrics:
    """
    Simulate load test metrics based on config and traffic.
    
    This is a simplified model that:
    - Higher CPU = lower latency (up to a point)
    - Higher memory = more stable performance
    - More replicas = higher throughput
    - Memory constraints cause latency spikes
    - CPU constraints cause throughput limits
    """
    cpu_cores = cpu / 1000
    memory_gb = memory / 1024
    
    base_throughput = traffic.target_rps
    target_cpu = 2000
    target_memory = 4096
    target_replicas = 5
    
    cpu_factor = min(1.5, cpu / target_cpu)
    memory_factor = min(1.3, memory_gb / (target_memory / 1024))
    replica_factor = math.sqrt(replicas / target_replicas)
    
    resource_factor = (cpu_factor * 0.6 + memory_factor * 0.4)
    
    base_latency_p50 = 50 * (1 / resource_factor)
    base_latency_p95 = 150 * (1 / resource_factor)
    base_latency_p99 = 300 * (1 / resource_factor)
    
    vusers = (traffic.vusers_min + traffic.vusers_max) / 2
    load_factor = min(1.5, vusers / 500)
    
    variance = random.uniform(0.85, 1.15)
    
    latency_p50 = max(5, base_latency_p50 * load_factor * variance)
    latency_p95 = max(20, base_latency_p95 * load_factor * variance * 1.5)
    latency_p99 = max(50, base_latency_p99 * load_factor * variance * 2)
    
    if cpu < 500:
        latency_p99 *= 1.5
    if memory < 512:
        latency_p99 *= 1.3
    
    throughput = base_throughput * replica_factor * resource_factor * variance
    throughput = min(throughput, replicas * 2000)
    
    if cpu < 500:
        throughput *= 0.6
    if memory < 512:
        throughput *= 0.7
    
    error_rate = 0.5
    if cpu < 500:
        error_rate += 2.0
    if memory < 512:
        error_rate += 1.5
    if replicas == 1:
        error_rate += 1.0
    
    error_rate = max(0.1, error_rate * random.uniform(0.5, 1.5))
    
    return Metrics(
        latency_p50=round(latency_p50, 2),
        latency_p95=round(latency_p95, 2),
        latency_p99=round(latency_p99, 2),
        throughput=round(throughput, 2),
        error_rate=round(error_rate, 2)
    )


def calculate_score(metrics: Metrics, cost_monthly: float, 
                    baseline_cost: float) -> float:
    """
    Calculate overall score (0-10) for a configuration.
    
    Weighted: latency (30%), throughput (30%), cost (20%), errors (20%)
    """
    from cost_calculator import calculate_cost_score
    
    latency_score = max(0, min(10, 10 - (metrics.latency_p99 / 100)))
    
    target_rps = 1000
    throughput_score = min(10, (metrics.throughput / target_rps) * 10)
    
    cost_score = calculate_cost_score(cost_monthly, baseline_cost)
    
    error_score = max(0, 10 - metrics.error_rate * 10)
    
    score = (
        latency_score * 0.30 +
        throughput_score * 0.30 +
        cost_score * 0.20 +
        error_score * 0.20
    )
    
    return round(score, 2)


def find_winner(results: List[Dict]) -> Optional[Dict]:
    """Find the best configuration (highest score)."""
    if not results:
        return None
    
    return max(results, key=lambda r: r["score"])
