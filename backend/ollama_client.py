"""
Ollama client for AI-powered load testing recommendations.
"""

import json
import requests
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2"
    timeout: int = 60


class OllamaClient:
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.base_url = self.config.base_url.rstrip("/")
        self._current_model = self.config.model
    
    @property
    def model(self) -> str:
        return self._current_model
    
    @model.setter
    def model(self, value: str):
        self._current_model = value
        self.config.model = value
    
    def set_model(self, model: str):
        """Set the active model."""
        self._current_model = model
        self.config.model = model
        return self._current_model
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            return []
        except:
            return []
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response from Ollama."""
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 512
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: {response.status_code}"
        except requests.exceptions.Timeout:
            return "Error: Request timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def check_health(self) -> Dict[str, Any]:
        """Check Ollama health status."""
        models = self.list_models()
        return {
            "available": self.is_available(),
            "models": models,
            "default_model": self.config.model if self.is_available() else None,
            "url": self.base_url
        }


class LoadTestAdvisor:
    """AI advisor for load testing decisions."""
    
    SYSTEM_PROMPT = """You are an expert Load Testing and DevOps engineer.
    Analyze load test results and provide clear, actionable recommendations.
    Focus on:
    - Performance optimization
    - Cost reduction
    - Infrastructure scaling
    - Error analysis
    Provide concise, specific advice in plain text."""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def analyze_results(self, test_results: Dict[str, Any]) -> str:
        """Analyze test results and provide recommendations."""
        
        metrics = test_results.get("metrics", {})
        config = test_results.get("config", {})
        cost = test_results.get("cost_monthly", 0)
        score = test_results.get("score", 0)
        
        prompt = f"""Analyze this load test result and provide recommendations:

**Configuration:**
- CPU: {config.get('cpu', 'N/A')}m
- Memory: {config.get('memory', 'N/A')}Mi
- Replicas: {config.get('replicas', 'N/A')}

**Performance Metrics:**
- P50 Latency: {metrics.get('latency_p50', 'N/A')}ms
- P95 Latency: {metrics.get('latency_p95', 'N/A')}ms
- P99 Latency: {metrics.get('latency_p99', 'N/A')}ms
- Throughput: {metrics.get('throughput', 'N/A')} rps
- Error Rate: {metrics.get('error_rate', 'N/A')}%

**Cost:**
- Monthly Cost: ${cost}

**Score:** {score}/10

Provide:
1. Key findings (2-3 bullets)
2. Specific recommendations (2-3 bullets)
3. Should we scale up, scale down, or keep current config?"""
        
        return self.ollama.generate(prompt, self.SYSTEM_PROMPT)
    
    def compare_configs(self, configs: List[Dict[str, Any]]) -> str:
        """Compare multiple configurations and recommend the best."""
        
        config_summaries = []
        for i, cfg in enumerate(configs[:5]):
            metrics = cfg.get("metrics", {})
            config_summaries.append(f"""
Config {i+1}:
- CPU: {cfg.get('config', {}).get('cpu', 'N/A')}m
- Memory: {cfg.get('config', {}).get('memory', 'N/A')}Mi  
- Replicas: {cfg.get('config', {}).get('replicas', 'N/A')}
- P99 Latency: {metrics.get('latency_p99', 'N/A')}ms
- Throughput: {metrics.get('throughput', 'N/A')} rps
- Error Rate: {metrics.get('error_rate', 'N/A')}%
- Cost: ${cfg.get('cost_monthly', 'N/A')}/mo
- Score: {cfg.get('score', 'N/A')}/10
""")
        
        prompt = f"""Compare these load test configurations and recommend the best one:

{''.join(config_summaries)}

Based on balancing performance and cost, which configuration do you recommend and why?
Be specific about trade-offs."""
        
        return self.ollama.generate(prompt, self.SYSTEM_PROMPT)
    
    def suggest_next_test(self, current_config: Dict, metrics: Dict) -> str:
        """Suggest the next test configuration to try."""
        
        prompt = f"""Current configuration under test:
- CPU: {current_config.get('cpu', 'N/A')}m
- Memory: {current_config.get('memory', 'N/A')}Mi
- Replicas: {current_config.get('replicas', 'N/A')}

Current metrics:
- P99 Latency: {metrics.get('latency_p99', 'N/A')}ms
- Throughput: {metrics.get('throughput', 'N/A')} rps
- Error Rate: {metrics.get('error_rate', 'N/A')}%

If latency is high, suggest a config with more CPU.
If throughput is low, suggest more replicas.
If cost is high, suggest reducing resources.

What should we test next? Respond with a specific configuration."""
        
        return self.ollama.generate(prompt, self.SYSTEM_PROMPT)
    
    def generate_summary(self, test_name: str, results: List[Dict]) -> str:
        """Generate a summary report of all test results."""
        
        if not results:
            return "No results to summarize."
        
        winner = max(results, key=lambda x: x.get("score", 0))
        worst = min(results, key=lambda x: x.get("score", 0))
        
        avg_latency = sum(r.get("metrics", {}).get("latency_p99", 0) for r in results) / len(results)
        avg_cost = sum(r.get("cost_monthly", 0) for r in results) / len(results)
        
        prompt = f"""Generate a summary report for load test: {test_name}

Results Summary:
- Total configurations tested: {len(results)}
- Best Score: {winner.get('score', 'N/A')}/10
  - Config: {winner.get('config', {})}
  - P99 Latency: {winner.get('metrics', {}).get('latency_p99', 'N/A')}ms
  - Cost: ${winner.get('cost_monthly', 'N/A')}/mo
- Worst Score: {worst.get('score', 'N/A')}/10
  - P99 Latency: {worst.get('metrics', {}).get('latency_p99', 'N/A')}ms
  - Cost: ${worst.get('cost_monthly', 'N/A')}/mo
- Average P99 Latency: {avg_latency:.0f}ms
- Average Cost: ${avg_cost:.2f}/mo

Provide a concise executive summary with the top 3 recommendations."""

        return self.ollama.generate(prompt, self.SYSTEM_PROMPT)


def parse_config_from_ai_response(response: str) -> Optional[Dict]:
    """Parse a configuration from AI response text."""
    import re
    
    cpu_match = re.search(r'cpu[:\s]+(\d+)', response, re.IGNORECASE)
    memory_match = re.search(r'memory[:\s]+(\d+)', response, re.IGNORECASE)
    replicas_match = re.search(r'replica[s]?[:\s]+(\d+)', response, re.IGNORECASE)
    
    if cpu_match or memory_match or replicas_match:
        return {
            "cpu": int(cpu_match.group(1)) if cpu_match else None,
            "memory": int(memory_match.group(1)) if memory_match else None,
            "replicas": int(replicas_match.group(1)) if replicas_match else None
        }
    
    return None
