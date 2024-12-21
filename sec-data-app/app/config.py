import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

from .logger import get_logger
from .exceptions import ConfigurationError

logger = get_logger('config')

class ConfigManager:
    """
    Centralized configuration management with multi-source support.
    Supports environment variables, .env files, and YAML configuration.
    """
    
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        """
        Singleton implementation to ensure single configuration instance.
        """
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path (str, optional): Path to YAML configuration file
        """
        if not self._config:
            # Load environment variables
            load_dotenv()
            
            # Load YAML configuration if path provided
            if config_path and os.path.exists(config_path):
                self._load_yaml_config(config_path)
            
            # Load environment-specific configurations
            self._load_environment_config()
            
            logger.info("Configuration initialized successfully")

    def _load_yaml_config(self, config_path: str):
        """
        Load configuration from YAML file.
        
        Args:
            config_path (str): Path to YAML configuration file
        """
        try:
            with open(config_path, 'r') as config_file:
                yaml_config = yaml.safe_load(config_file)
                self._config.update(yaml_config)
                logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load YAML configuration: {e}")
            raise ConfigurationError(f"Invalid configuration file: {config_path}")

    def _load_environment_config(self):
        """
        Load configuration from environment variables.
        Prioritize environment variables over file-based configurations.
        """
        env_mappings = {
            'SEC_API_BASE_URL': 'sec.api.base_url',
            'REDIS_HOST': 'cache.redis.host',
            'REDIS_PORT': 'cache.redis.port',
            'LOG_LEVEL': 'logging.level',
            'DEBUG_MODE': 'app.debug_mode'
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert to appropriate type
                if config_key.endswith('port'):
                    value = int(value)
                elif config_key.endswith('debug_mode'):
                    value = value.lower() in ['true', '1', 'yes']
                
                self._set_nested_config(config_key, value)

    def _set_nested_config(self, key: str, value: Any):
        """
        Set nested configuration value.
        
        Args:
            key (str): Dot-separated configuration key
            value (Any): Configuration value
        """
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve configuration value with dot notation support.
        
        Args:
            key (str): Dot-separated configuration key
            default (Any, optional): Default value if key not found
        
        Returns:
            Any: Configuration value
        """
        try:
            keys = key.split('.')
            value = self._config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.warning(f"Configuration key not found: {key}")
            return default

    def reload(self, config_path: str = None):
        """
        Reload configuration from file and environment.
        
        Args:
            config_path (str, optional): Path to YAML configuration file
        """
        self._config.clear()
        self.__init__(config_path)

    def validate_config(self):
        """
        Validate critical configuration parameters.
        
        Raises:
            ConfigurationError: If critical configuration is missing or invalid
        """
        critical_keys = [
            'sec.api.base_url',
            'cache.redis.host',
            'logging.level'
        ]

        for key in critical_keys:
            if self.get(key) is None:
                raise ConfigurationError(f"Missing critical configuration: {key}")

# Global configuration manager instance
config = ConfigManager(
    config_path=os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'config', 
        'app_config.yaml'
    )
)
