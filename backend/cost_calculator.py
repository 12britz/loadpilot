"""
Cloud cost calculator for Kubernetes pod resources.
"""

CLOUD_PRICING = {
    "aws": {
        "regions": {
            "us-east-1": {
                "cpu_hourly": 0.0236,
                "memory_hourly_gb": 0.0059,
                "cluster_monthly": 73.00
            },
            "us-west-2": {
                "cpu_hourly": 0.0256,
                "memory_hourly_gb": 0.0065,
                "cluster_monthly": 73.00
            },
            "eu-west-1": {
                "cpu_hourly": 0.0270,
                "memory_hourly_gb": 0.0071,
                "cluster_monthly": 84.00
            },
            "ap-southeast-1": {
                "cpu_hourly": 0.0280,
                "memory_hourly_gb": 0.0076,
                "cluster_monthly": 84.00
            }
        }
    },
    "gcp": {
        "regions": {
            "us-central1": {
                "cpu_hourly": 0.0335,
                "memory_hourly_gb": 0.0045,
                "cluster_monthly": 73.00
            },
            "us-east1": {
                "cpu_hourly": 0.0335,
                "memory_hourly_gb": 0.0045,
                "cluster_monthly": 73.00
            }
        }
    },
    "azure": {
        "regions": {
            "eastus": {
                "cpu_hourly": 0.0240,
                "memory_hourly_gb": 0.0059,
                "cluster_monthly": 74.00
            }
        }
    }
}

HOURS_PER_MONTH = 730


def get_pricing(cloud_provider: str, region: str) -> dict:
    provider = CLOUD_PRICING.get(cloud_provider.lower(), CLOUD_PRICING["aws"])
    region_data = provider.get("regions", {}).get(region, provider["regions"]["us-east-1"])
    return region_data


def calculate_pod_hourly_cost(cpu_millicores: int, memory_mb: int, 
                               cloud_provider: str = "aws", 
                               region: str = "us-east-1") -> float:
    """
    Calculate hourly cost for a single pod.
    
    Args:
        cpu_millicores: CPU in millicores (e.g., 500 = 0.5 CPU)
        memory_mb: Memory in MB
        cloud_provider: aws, gcp, or azure
        region: Cloud region
    
    Returns:
        Hourly cost in dollars
    """
    pricing = get_pricing(cloud_provider, region)
    
    cpu_cores = cpu_millicores / 1000
    memory_gb = memory_mb / 1024
    
    cpu_cost = cpu_cores * pricing["cpu_hourly"]
    memory_cost = memory_gb * pricing["memory_hourly_gb"]
    
    return cpu_cost + memory_cost


def calculate_monthly_cost(cpu_millicores: int, memory_mb: int, replicas: int,
                            cloud_provider: str = "aws", 
                            region: str = "us-east-1") -> float:
    """
    Calculate monthly cost for a pod configuration.
    
    Args:
        cpu_millicores: CPU in millicores
        memory_mb: Memory in MB
        replicas: Number of pod replicas
        cloud_provider: aws, gcp, or azure
        region: Cloud region
    
    Returns:
        Monthly cost in dollars
    """
    pricing = get_pricing(cloud_provider, region)
    pod_hourly = calculate_pod_hourly_cost(cpu_millicores, memory_mb, cloud_provider, region)
    
    pods_monthly = pod_hourly * HOURS_PER_MONTH * replicas
    cluster_monthly = pricing["cluster_monthly"]
    
    return round(pods_monthly + cluster_monthly, 2)


def calculate_cost_score(cost: float, baseline_cost: float) -> float:
    """
    Calculate a cost score from 0-10 (higher is better).
    
    A config that costs half the baseline gets score 10.
    A config that costs 2x the baseline gets score 0.
    """
    if baseline_cost <= 0:
        return 10.0
    
    ratio = cost / baseline_cost
    
    if ratio <= 0.5:
        return 10.0
    elif ratio >= 2.0:
        return 0.0
    else:
        return round(10 - (ratio - 0.5) * 10 / 1.5, 2)


def format_cost(cost: float) -> str:
    """Format cost for display."""
    if cost >= 1000:
        return f"${cost:,.0f}"
    elif cost >= 100:
        return f"${cost:.0f}"
    else:
        return f"${cost:.2f}"
