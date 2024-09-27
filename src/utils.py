import json
import os.path as osp
from contraints import conditional_constraints


class config_param:
    def __init__(self, name, default_value, self_range, index):
        self.name = name
        self.default_value = default_value
        self.self_range = self_range
        self.index = index

    def check_self_validity(self, new_value):
        if new_value in self.self_range:
            return True
        else:
            return False

class config_params:
    def __init__(self, params, conditional_constraints):
        self.params = params
        self.amount = len(self.params)
        self.params_map = {}
        self.conditional_constraints = conditional_constraints
        for param in self.params:
            self.params_map[param.name] = param


class classification_metrics:
    def __init__(self, metrics):
        self.metrics = metrics
        self.value = None
        self.constraints = None

class output_params:
    def __init__(self, Power, Resource_Utilisation, Benchmark):
        self.power = Power
        self.resource = Resource_Utilisation
        self.benchmark = Benchmark
        self.metric_amounts = len(self.power.metrics) + len(self.resource.metrics) + len(self.benchmark.metrics) 


class object_cpu_info:
    def __init__(self, name, params, output_objs):
        self.cpu_name = name
        self.config_params = params
        self.supported_output_objs = output_objs
        self.target_fpga = None
        self.tunable_params = []  
        self.target_objs = []

    def add_target_fpga(self, target_fpga):
        self.target_fpga = target_fpga

    def update_tunable_param(self, target_tunable_param):
        for param in self.config_params.params:
            if param.name == target_tunable_param:
                self.tunable_params.append(param.index)
                return True
        return False        

    def update_target_objs(self, target_objs):
        self.target_objs.append(target_objs)

    def check_parameter_validity(self, new_design):
        if len(new_design) != len(self.config_params):
            raise ValueError("The number of parameters does not match the number of configurable parameters")
        # Self constraints
        for param in self.config_params:
            if not param.check_self_validity(new_design[param.index]):
                return False
        # Cofnitional constraints
            #TODO
        return True
    
    # def check_fpga_deployability(self, synthesis_results):
    #     if self.target_fpga is None:
    #         return False
    #     return True
    
    def debug_print(self):
        print(f"CPU Name is {self.cpu_name}")
        print(f"All Supported Parameters are {self.config_params.params_map.keys()}")
        print(f"Tunable Parameters are {self.tunable_params}")
        print(f"Target Objs are {self.target_objs}")
        print(f"Target FPGA is {self.target_fpga['Part']}")


def read_cpu_info_from_json(json_file):
    if not osp.exists(json_file):
        raise FileNotFoundError(f"File {json_file} not found")
    with open(json_file, 'r') as file:
        data = json.load(file)

    ## Build config_params
    tmp_config_params = []
    param_index = 0
    for param, settings in data["Configurable_Params"].items():
        tmp_param = config_param(param, settings["default"], settings["self_range"], param_index)
        tmp_config_params.append(tmp_param)
        param_index += 1

    # Identify conditional constraints
    extracted_conditional_constraints = None
    if data["Conditional_Constraints"] is not None:
        #TODO
        pass
    extracted_config_params = config_params(tmp_config_params, extracted_conditional_constraints)

    ## Build output objective library    
    for classification, settings in data["PPA"].items():
        metrics = []
        for m in settings.keys():
            metrics.append(m)
        if classification == "Power":
            tmp_power = classification_metrics(metrics)
        elif classification == "Resource_Utilisation":
            tmp_resource = classification_metrics(metrics)
        elif classification == "Benchmark":
            tmp_benchmark = classification_metrics(metrics)        
    output_lib = output_params(tmp_power, tmp_resource, tmp_benchmark)
    # Build CPU object
    cpu_info = object_cpu_info(data["CPU_Name"], extracted_config_params, output_lib)
    return cpu_info

def read_fpga_info_from_json(fpga_series_number):
    with open('../dataset/fpga/fpga_rc.json', 'r') as file:
        data = json.load(file)
    for device in data:
        if device["Part"] == fpga_series_number:
            return device
    return None  # Return None if the part number is not found


if __name__ == '__main__':
    read_cpu_info_from_json('../dataset/constraints/RocketChip_Config.json')