import yaml
import os
from typing import Optional, List
from .label_criterion import LabelCriterion


class Config:
    def __init__(self, config_file: str):
        self.config_file = config_file

        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file {self.config_file} not found")

        with open(self.config_file, "r", encoding="utf-8") as stream:
            try:
                self.config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def __getitem__(self, key: str):
        return self.config.get(key)

    @property
    def target(self) -> str:
        return self["target"]

    @property
    def duration_millis(self) -> int:
        return self["duration_millis"]

    @property
    def realtime_diagram(self) -> bool:
        return self["realtime_diagram"]

    @property
    def page_update_interval(self) -> int:
        return self["page_update_interval"]

    @property
    def write_logs(self) -> bool:
        return self["write_logs"]

    @property
    def disable_gpu(self) -> bool:
        return self["disable_gpu"]

    @property
    def total_only(self) -> bool:
        return self["total_only"]

    @property
    def port(self) -> int:
        return self["advanced"]["port"]

    @property
    def history_upperbound(self) -> int:
        return self["advanced"]["history_upperbound"]

    @property
    def cpu_duration_millis(self) -> int:
        return self["advanced"]["cpu_duration_millis"]

    @property
    def gpu_duration_millis(self) -> int:
        return self["advanced"]["gpu_duration_millis"]

    @property
    def label_criteria(self) -> List[LabelCriterion]:
        criteria = self["advanced"]["label_criteria"]
        ret = []
        for criterion in criteria:
            ret.append(LabelCriterion(criterion["keyword"], criterion["label"]))
        return ret
