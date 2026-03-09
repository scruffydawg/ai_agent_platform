import os
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from apps.api.settings import get_settings, AppSettings

logger = logging.getLogger(__name__)

class ConfigService:
    """
    Service for managing application configuration and settings.
    Bridges Pydantic BaseSettings with dynamic updates and persistence.
    """
    def __init__(self, settings: AppSettings):
        self._settings = settings
        self._dynamic_overrides: Dict[str, Any] = {}
        
        # Load persistent overrides if they exist
        self._override_file = "config_overrides.json"
        self._load_overrides()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value, checking dynamic overrides first."""
        if key in self._dynamic_overrides:
            return self._dynamic_overrides[key]
        return getattr(self._settings, key, default)

    def update(self, new_settings: Dict[str, Any]):
        """Update dynamic settings and persist them."""
        for k, v in new_settings.items():
            if hasattr(self._settings, k):
                self._dynamic_overrides[k] = v
                logger.info(f"Setting override: {k}={v}")
        
        self._save_overrides()

    def _load_overrides(self):
        if os.path.exists(self._override_file):
            try:
                with open(self._override_file, "r") as f:
                    self._dynamic_overrides = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config overrides: {e}")

    def _save_overrides(self):
        try:
            with open(self._override_file, "w") as f:
                json.dump(self._dynamic_overrides, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config overrides: {e}")

    def dict(self) -> Dict[str, Any]:
        """Return full configuration as a flat dictionary."""
        base = self._settings.dict()
        base.update(self._dynamic_overrides)
        return base

# Singleton
config_service = ConfigService(get_settings())
