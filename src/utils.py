import json
import os.path as osp


class config_param:
    def __init__(self, name, default_value, self_range):
        self.name = name
        self.default_value = default_value
        self.self_range = self_range

class classification_metrics:
    def __init__(self, class_name, metrics):
        self.class_name = class_name
        self.metrics = metrics
        self.value = None
        self.constraints = None

class output_params:
    def __init__(self, ):
        self.output_library = {}


class object_cpu_info:
    def __init__(self, name, config_params, output_params):
        self.cpu_name = name
        self.config_params = config_params
        self.output_params = output_params
        self.target_fpga = None

    def add_target_fpga(self, target_fpga):
        self.target_fpga = target_fpga


def read_from_json(json_file):
    if not osp.exists(json_file):
        raise FileNotFoundError(f"File {json_file} not found")
    with open(json_file, 'r') as file:
        data = json.load(file)
    
    # Build config_params
    config_params = []
    for param, settings in data["Configurable_Params"].items():
        tmp_param = config_param(param, settings["default"], settings["self_range"])
        config_params.append(tmp_param)

    # Build output library
    output_lib = {}
    for classification, settings in data["PPA"].items():
        metrics = []
        for m in settings.keys():
            metrics.append(m)
        tmp_class = classification_metrics(classification, metrics)
        output_lib[classification] = tmp_class
    
    # Build CPU object
    cpu_info = object_cpu_info(data["CPU_Name"], config_params, output_lib)
    return cpu_info

if __name__ == '__main__':
    read_from_json('../dataset/constraints/RocketChip_Config.json')