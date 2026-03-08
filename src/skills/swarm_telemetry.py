import psutil
import asyncio
import httpx
import socket
import os
from src.utils.logger import logger
from src.config import TAILNET_NODES

class SwarmTelemetry:
    def __init__(self):
        self.nodes = TAILNET_NODES
        self.local_node = "tai_mae" 

    def check_lan_exposure(self):
        """Checks if ports are open on the local network (non-loopback, non-Tailscale)."""
        ports = [22, 80, 443, 8000, 6333, 5432]
        exposed_ports = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                # We flag if it's listening on 0.0.0.0 (all) or a non-loopback/non-tailscale IP
                ip = conn.laddr.ip
                if conn.status == 'LISTEN' and conn.laddr.port in ports:
                    if ip == '0.0.0.0' or (not ip.startswith('127.') and not ip.startswith('100.')):
                        exposed_ports.append(conn.laddr.port)
        except:
            pass
        return sorted(list(set(exposed_ports)))

    def get_llm_instances(self):
        """Detects active vLLM and Ollama processes."""
        instances = []
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                cmdline = " ".join(proc.info['cmdline'] or [])
                if 'vllm' in cmdline.lower():
                    instances.append("vLLM")
                elif 'ollama' in cmdline.lower():
                    instances.append("Ollama")
            except:
                pass
        return list(set(instances))

    async def get_local_stats(self):
        """Gets CPU, RAM, GPU, LAN, and LLM stats."""
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        
        # GPU Check (Mocked)
        gpu = 0
        if os.path.exists("/usr/bin/nvidia-smi"):
            gpu = 45 # Mock load for prototype

        return {
            "status": "online",
            "cpu": cpu,
            "ram": ram,
            "gpu": gpu,
            "lan_exposed": self.check_lan_exposure(),
            "llm_instances": self.get_llm_instances(),
            "vllm_tps": 12.5 
        }

    async def get_remote_stats(self, node_key, dns):
        """Polls remote nodes (Mocked for Swarm Dashboard variety)."""
        try:
            # In a real swarm, this hits nodes via Tailscale MagicDNS
            if "sienna" in node_key:
                return {"status": "online", "cpu": 15, "ram": 32, "gpu": 0, "lan_exposed": [], "llm_instances": ["vLLM"], "vllm_tps": 40}
            if "dash" in node_key:
                return {"status": "online", "cpu": 5, "ram": 12, "gpu": 0, "lan_exposed": [5432], "llm_instances": [], "vllm_tps": 0}
            if "pi" in node_key:
                return {"status": "online", "cpu": 82, "ram": 60, "gpu": 0, "lan_exposed": [22], "llm_instances": ["Ollama"], "vllm_tps": 0}
            return {"status": "unknown", "cpu": 0, "ram": 0, "gpu": 0, "lan_exposed": [], "llm_instances": []}
        except:
            return {"status": "offline", "cpu": 0, "ram": 0, "gpu": 0, "lan_exposed": [], "llm_instances": []}

    async def get_swarm_status(self):
        """Aggregates status from all nodes in the Tailnet."""
        tasks = []
        for key, dns in self.nodes.items():
            if key == self.local_node:
                tasks.append(self.get_local_stats())
            else:
                tasks.append(self.get_remote_stats(key, dns))
        
        results = await asyncio.gather(*tasks)
        return {key: results[i] for i, key in enumerate(self.nodes.keys())}

swarm_telemetry = SwarmTelemetry()
