from pydantic import BaseModel, Field
from typing import Optional, List


class ResourceConfig(BaseModel):
    cpu_min: int = Field(ge=100, le=8000, description="Min CPU in millicores")
    cpu_max: int = Field(ge=100, le=8000)
    cpu_step: int = Field(ge=100, le=1000, default=250)
    memory_min: int = Field(ge=128, le=32768, description="Min memory in MB")
    memory_max: int = Field(ge=128, le=32768)
    memory_step: int = Field(ge=128, le=2048, default=256)


class ReplicaConfig(BaseModel):
    min: int = Field(ge=1, le=10, default=1)
    max: int = Field(ge=1, le=50, default=5)


class TrafficConfig(BaseModel):
    ramp_up: int = Field(ge=10, le=600, default=60, description="Ramp-up duration in seconds")
    peak: int = Field(ge=30, le=3600, default=120)
    ramp_down: int = Field(ge=10, le=600, default=60)
    vusers_min: int = Field(ge=10, le=10000, default=100)
    vusers_max: int = Field(ge=10, le=10000, default=1000)
    target_rps: int = Field(ge=10, le=100000, default=1000)


class TestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    cloud_provider: str = Field(default="aws")
    region: str = Field(default="us-east-1")
    resource_config: ResourceConfig = Field(default_factory=ResourceConfig)
    replica_config: ReplicaConfig = Field(default_factory=ReplicaConfig)
    traffic_config: TrafficConfig = Field(default_factory=TrafficConfig)


class JmxTestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    cloud_provider: str = Field(default="aws")
    region: str = Field(default="us-east-1")
    threads: int = Field(ge=1, le=10000, default=100, description="Number of virtual users")
    ramp_up: int = Field(ge=0, le=3600, default=60, description="Ramp-up time in seconds")
    duration: int = Field(ge=10, le=3600, default=300, description="Test duration in seconds")


class ConfigSpec(BaseModel):
    cpu: int
    memory: int
    replicas: int


class Metrics(BaseModel):
    latency_p50: float
    latency_p95: float
    latency_p99: float
    throughput: float
    error_rate: float


class JmxMetrics(BaseModel):
    latency_p50: float
    latency_p95: float
    latency_p99: float
    latency_avg: float
    throughput: float
    error_rate: float
    total_requests: int
    failed_requests: int


class ResultResponse(BaseModel):
    id: str
    test_id: str
    config: ConfigSpec
    metrics: Metrics
    cost_monthly: float
    score: float
    timestamp: str


class JmxResultResponse(BaseModel):
    id: str
    test_id: str
    jmx_filename: str
    threads: int
    ramp_up: int
    duration: int
    metrics: JmxMetrics
    cost_monthly: float
    score: float
    timestamp: str
    output_path: Optional[str] = None


class TestResponse(BaseModel):
    id: str
    name: str
    test_type: str = Field(default="matrix", description="matrix or jmx")
    cloud_provider: str
    region: str
    resource_config: Optional[ResourceConfig] = None
    replica_config: Optional[ReplicaConfig] = None
    traffic_config: Optional[TrafficConfig] = None
    jmx_config: Optional[JmxTestCreate] = None
    status: str
    created_at: str
    completed_at: Optional[str] = None
    total_configs: int = 0
    results_count: int = 0


class TestDetailResponse(TestResponse):
    results: List[ResultResponse] = []
    jmx_results: List[JmxResultResponse] = []
    winner: Optional[ResultResponse] = None


class DashboardStats(BaseModel):
    total_tests: int
    completed_tests: int
    active_tests: int
    avg_cost_savings: float
    total_configs_tested: int


class TestListResponse(BaseModel):
    tests: List[TestResponse]
    stats: DashboardStats
