"""
Kubernetes integration for real cluster load testing.
"""

import os
import json
import time
import uuid
import yaml
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class ClusterStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class ClusterConfig:
    kubeconfig_path: Optional[str] = None
    context: Optional[str] = None
    namespace: str = "default"
    ingress_url: Optional[str] = None


@dataclass
class PodConfig:
    name: str
    cpu_millicores: int
    memory_mb: int
    image: str = "nginx"
    replicas: int = 1
    port: int = 80


class KubernetesClient:
    """Client for interacting with Kubernetes clusters."""
    
    def __init__(self):
        self._client = None
        self._config = None
        self._core_api = None
        self._apps_api = None
        self._networking_api = None
        self._custom_api = None
        self._status = ClusterStatus.DISCONNECTED
        self._cluster_info = None
    
    @property
    def status(self) -> ClusterStatus:
        return self._status
    
    @property
    def cluster_info(self) -> Optional[Dict]:
        return self._cluster_info
    
    def check_connection(self, kubeconfig_path: Optional[str] = None) -> Dict[str, Any]:
        """Check if we can connect to the cluster."""
        try:
            from kubernetes import client, config
            
            if kubeconfig_path and os.path.exists(kubeconfig_path):
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                try:
                    config.load_incluster_config()
                except:
                    config.load_kube_config()
            
            self._core_api = client.CoreV1Api()
            self._apps_api = client.AppsV1Api()
            
            v1_info = self._core_api.get_api_resources()
            cluster_name = "unknown"
            try:
                version = self._core_api.get_version()
                cluster_name = version.get('gitVersion', 'unknown')
            except:
                pass
            
            nodes = self._core_api.list_node()
            node_count = len(nodes.items)
            
            self._status = ClusterStatus.CONNECTED
            self._cluster_info = {
                "status": "connected",
                "cluster_name": cluster_name,
                "nodes": node_count,
                "api_version": v1_info.group_version,
            }
            
            return self._cluster_info
            
        except Exception as e:
            self._status = ClusterStatus.ERROR
            return {
                "status": "error",
                "error": str(e)
            }
    
    def disconnect(self):
        """Disconnect from the cluster."""
        self._client = None
        self._core_api = None
        self._apps_api = None
        self._status = ClusterStatus.DISCONNECTED
        self._cluster_info = None
    
    def get_namespaces(self) -> List[str]:
        """Get list of namespaces."""
        if not self._core_api:
            return []
        try:
            ns_list = self._core_api.list_namespace()
            return [ns.metadata.name for ns in ns_list.items]
        except:
            return []
    
    def deploy_test_pods(self, config: PodConfig, namespace: str = "default") -> Dict[str, Any]:
        """Deploy test pods with specific configuration."""
        if not self._apps_api or not self._core_api:
            raise Exception("Not connected to cluster")
        
        deployment_name = f"loadpilot-{config.name}-{uuid.uuid4().hex[:8]}"
        service_name = f"{deployment_name}-svc"
        
        deployment_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": deployment_name,
                "namespace": namespace,
                "labels": {
                    "app": "loadpilot",
                    "test": config.name
                }
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {
                    "matchLabels": {
                        "app": "loadpilot-test"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "loadpilot-test",
                            "test": config.name
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": "test-app",
                            "image": config.image,
                            "ports": [{"containerPort": config.port}],
                            "resources": {
                                "requests": {
                                    "cpu": f"{config.cpu_millicores}m",
                                    "memory": f"{config.memory_mb}Mi"
                                },
                                "limits": {
                                    "cpu": f"{config.cpu_millicores}m",
                                    "memory": f"{config.memory_mb}Mi"
                                }
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/", "port": config.port},
                                "initialDelaySeconds": 5,
                                "periodSeconds": 10
                            }
                        }]
                    }
                }
            }
        }
        
        service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": service_name,
                "namespace": namespace,
                "labels": {"app": "loadpilot"}
            },
            "spec": {
                "selector": {"app": "loadpilot-test"},
                "ports": [{"port": 80, "targetPort": config.port}]
            }
        }
        
        try:
            self._apps_api.create_namespaced_deployment(
                namespace=namespace,
                body=yaml.safe_load(yaml.dump(deployment_manifest))
            )
            
            self._core_api.create_namespaced_service(
                namespace=namespace,
                body=yaml.safe_load(yaml.dump(service_manifest))
            )
            
            time.sleep(5)
            
            pods = self._core_api.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"test={config.name}"
            )
            
            pod_ips = []
            for pod in pods.items:
                if pod.status.pod_ip:
                    pod_ips.append(pod.status.pod_ip)
            
            return {
                "deployment": deployment_name,
                "service": service_name,
                "namespace": namespace,
                "pods": len(pod_ips),
                "pod_ips": pod_ips,
                "status": "deployed"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def delete_test_resources(self, deployment_name: str, service_name: str, namespace: str = "default") -> bool:
        """Delete test deployment and service."""
        try:
            self._apps_api.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=client.V1DeleteOptions()
            )
            self._core_api.delete_namespaced_service(
                name=service_name,
                namespace=namespace,
                body=client.V1DeleteOptions()
            )
            return True
        except:
            return False
    
    def get_pod_metrics(self, namespace: str = "default") -> Dict[str, Any]:
        """Get resource metrics for pods."""
        if not self._core_api:
            return {}
        
        try:
            pods = self._core_api.list_namespaced_pod(namespace=namespace)
            metrics = []
            
            for pod in pods.items:
                if pod.status.phase != "Running":
                    continue
                    
                container_metrics = []
                for container in pod.status.container_statuses or []:
                    usage = container.usage if hasattr(container, 'usage') else {}
                    container_metrics.append({
                        "name": container.name,
                        "cpu_cores": usage.get('cpu', {}).get('nano_cores', 0) / 1e9,
                        "memory_bytes": usage.get('memory', {}).get('bytes', 0)
                    })
                
                metrics.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": pod.status.phase,
                    "pod_ip": pod.status.pod_ip,
                    "containers": container_metrics
                })
            
            return {"pods": metrics}
        except Exception as e:
            return {"error": str(e)}
    
    def scale_deployment(self, name: str, replicas: int, namespace: str = "default") -> bool:
        """Scale a deployment."""
        if not self._apps_api:
            return False
        
        try:
            self._apps_api.patch_namespaced_deployment_scale(
                name=name,
                namespace=namespace,
                body={"spec": {"replicas": replicas}}
            )
            return True
        except:
            return False


kubernetes_client = KubernetesClient()
