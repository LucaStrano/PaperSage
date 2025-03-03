import yaml
from typing import Dict, Any, Optional


class ConfigLoader:
    """
    Singleton class to load and manage configuration from config.yaml
    """
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """Load the configuration file and parse it into a structured dictionary"""
        config_path = "config.yaml"
        
        try:
            with open(config_path, 'r') as file:
                raw_config = yaml.safe_load(file)
                
            self._config = self._transform_config(raw_config)
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            raise
    
    def _transform_config(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform the YAML structure into a more accessible dictionary"""
        transformed = {}
        
        # Process each config section
        for section in raw_config.get('configs', []):
            for section_name, items in section.items():
                section_dict = {}
                
                # Extract key-value pairs from each item in the section
                for item in items:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            section_dict[key] = value
                
                transformed[section_name] = section_dict
        
        return transformed
    
    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration dictionary"""
        return self._config
    
    def get_section(self, section_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific configuration section"""
        return self._config.get(section_name)
    
    def get_value(self, section_name: str, key: str) -> Any:
        """Get a specific configuration value from a section"""
        section = self.get_section(section_name)
        if section:
            return section.get(key)
        return None
    
    def reload(self) -> None:
        """Reload the configuration file"""
        self._load_config()