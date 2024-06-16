import yaml
import os
from typing import Optional, List
from .label_criterion import LabelCriterion

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

    @property
    def target(self) -> str:
        return self['target']

    @property
    def duration_millis(self) -> int:
        return self['duration_millis']

    @property
    def output_file(self) -> str:
        return self['output_file']

    @property
    def realtime_diagram(self) -> bool:
        return self['realtime_diagram']

    @property
    def label_criteria(self) -> List[LabelCriterion]:
        criteria = self['advanced']['label_criteria']
        ret = []
        for criterion in criteria:
            ret.append(LabelCriterion(criterion['keyword'], criterion['label']))
        return ret
