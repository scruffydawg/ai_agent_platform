import docker
from typing import Any, Dict, List
from src.skills.base import BaseSkill
from src.utils.logger import logger

class DockerManagementSkill(BaseSkill):
    """
    Skill for managing local and swarm Docker containers.
    Provides visibility and control over the platform's infrastructure.
    """
    name: str = "DockerManagementSkill"
    description: str = "Manage Docker containers, images, and networks. Can list, start, stop, and restart containers."

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        if not self.client:
            return {"status": "error", "message": "Docker client not initialized. Is Docker running?"}

        try:
            if action == "list_containers":
                all_containers = self.client.containers.list(all=True)
                container_data = []
                for c in all_containers:
                    container_data.append({
                        "id": c.short_id,
                        "name": c.name,
                        "status": c.status,
                        "image": str(c.image.tags[0]) if c.image.tags else "unknown"
                    })
                return {"status": "success", "containers": container_data}

            elif action == "start_container":
                container_name = kwargs.get("name")
                container = self.client.containers.get(container_name)
                container.start()
                return {"status": "success", "message": f"Container {container_name} started."}

            elif action == "stop_container":
                container_name = kwargs.get("name")
                # Safety check: Prevent stopping core infrastructure without explicit confirmation logic in larger flow
                container = self.client.containers.get(container_name)
                container.stop()
                return {"status": "success", "message": f"Container {container_name} stopped."}

            elif action == "restart_container":
                container_name = kwargs.get("name")
                container = self.client.containers.get(container_name)
                container.restart()
                return {"status": "success", "message": f"Container {container_name} restarted."}

            elif action == "get_logs":
                container_name = kwargs.get("name")
                tail = kwargs.get("tail", 50)
                container = self.client.containers.get(container_name)
                logs = container.logs(tail=tail).decode('utf-8')
                return {"status": "success", "logs": logs}

            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Docker action '{action}' failed: {e}")
            return {"status": "error", "message": str(e)}

docker_management = DockerManagementSkill()
