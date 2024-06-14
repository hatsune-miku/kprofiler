import yaml
import os
from typing import Optional

class Config:
    def __init__(self, config_file: str):
        self.config_file = config_file

        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f'Config file {self.config_file} not found')

        with open(self.config_file, 'r', encoding='utf-8') as stream:
            try:
                self.config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    
    def __getitem__(self, key: str):
        return self.config.get(key)

    def get_target(self, default_value: Optional[str] = None) -> str:
        return self['target'] or default_value
