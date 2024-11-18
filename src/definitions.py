import json
import math
import os.path as osp
from design_methods.format_constraints import Input_Constraints
from constraints import target_fpga_info
from design_methods.utils import get_device, get_tensor_type

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
        self.params = params     # self.params = list of config_param variables.
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

class target_benchmark_metrics:
    def __init__(self, benchmark_name, benchmark_activated_metrics):
        self.name = benchmark_name
        self.activated_benchmark_metric = {
            "exe_time"   :  "exe_time" in benchmark_activated_metrics,
            "throughput" :  "throughput" in benchmark_activated_metrics,
            "mcycles"    :  "mcycles" in benchmark_activated_metrics,
            "minstret"   :  "minstret" in benchmark_activated_metrics                  
                                           }
            

class output_params:
    def __init__(self, Power, Resource_Utilisation, Benchmark, Timing):
        self.power = Power
        self.resource = Resource_Utilisation
        self.benchmark = Benchmark
        self.timing = Timing
        self.metric_amounts = len(self.power.metrics)+ len(self.resource.metrics) + len(self.benchmark.metrics) * 4 + len(self.timing.metrics)

class Param_Space_Info:
    """Class to store all the related input information"""
    def __init__(self, input_dim, input_scales, input_normalized_factor, input_exp, input_offsets, input_names, input_constraints, input_categorical, self_constraints, conditional_constraints):
        self.input_dim = input_dim
        self.input_scales = input_scales
        self.input_normalized_factor = input_normalized_factor
        self.input_exp = input_exp
        self.input_offsets = input_offsets
        self.input_names = input_names
        self.constraints = input_constraints
        self.constants = None
        self.self_constraints = self_constraints
        self.conditional_constraints = conditional_constraints
        self.input_categorical = input_categorical

class Objective_Info:
    """Class to store all the related output information"""
    def __init__(self, obj_to_optimise, output_constraints, optimisation_target):
        self.obj_to_optimise = obj_to_optimise
        self.output_constraints = output_constraints
        self.optimisation_target = optimisation_target
        self.obj_to_optimise_dim = len(obj_to_optimise)
        self.obj_to_evaluate_dim = self.obj_to_optimise_dim + len(output_constraints)
        self.obj_to_optimise_index = list(range(self.obj_to_optimise_dim))



class object_cpu_info:
    def __init__(self, name, params, output_objs):
        self.cpu_name = name
        self.config_params = params
        self.supported_output_objs = output_objs
        self.tunable_params_index = []  
        self.tunable_params_name = []
        self.target_benchmark = []
        self.param_space_info = None
        self.objective_space_info = None
        self.device = get_device()
        self.t_type = get_tensor_type()


    def update_tunable_param(self, target_tunable_param):
        for param in self.config_params.params:
            if param.name == target_tunable_param:
                self.tunable_params_index.append(param.index)
                self.tunable_params_name.append(target_tunable_param)
                return True
        return False        

    def update_target_benchmark(self, target_benchmark, target_benchmark_metric):
        self.target_benchmark.append(target_benchmark_metrics(target_benchmark, target_benchmark_metric))

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
    
    def debug_print(self):
        print(f"CPU Name is {self.cpu_name}")
        print(f"All Supported Parameters are {self.config_params.params_map.keys()}")
        print(f"Tunable Parameters are {self.tunable_params_index}")
        print(f"Target Objs are {self.target_benchmark}")
    
    def display_summary(self):
        print("\n<--------------Settings Summary------------->")
        print(f"CPU Name is {self.cpu_name}")
        print(f"Configurable Parameters {self.tunable_params_name}")
        print(f"Benchmark and Metrics include: ")
        for benchmark in self.target_benchmark:
            print(f"Name: {benchmark.name} Metrics : {benchmark.activated_benchmark_metric}")


    def parse_proc_spec(self, design_spec):
        """this function is used to parse the constraints set by the CPU, it will investigate the constraints only related to the parameters to be tuned"""
        # Define dictionaries to store the parsed data
        if not osp.exists(design_spec):
            raise FileNotFoundError(f"File {design_spec} not found")
        with open(design_spec, 'r') as file:
            spec_content = json.load(file)

        self_constraints = {}
        input_constant = {}
        conditional_constraints = []
        output_objective = {}
        output_constraints = {}
        optimisation_task_name = spec_content["optimisation_task_name"]

        for param in spec_content["configurable_params"]:
            # Define a flag to track the section type
            param_name = param["var"]
            if param["data_type"] == "Int":
                scale = int(param["scale"])
                exp = int(param["exp"])
                self_constraints[param_name] = [int(param["range"][0]), int(param["range"][1]), scale, exp, param["data_type"]]
            else:
                self_constraints[param_name] = [param["range"], param["data_type"]]
            # update tunable parameters
            if not self.update_tunable_param(param_name):
                raise ValueError(f"The parameter {param_name} does not exist in the database. Please try again.")
        
        for const_param in spec_content["constant_params"]:
            input_constant[const_param["var"]] = const_param["value"]
            if not self.update_tunable_param(const_param["var"]):
                raise ValueError(f"The parameter does not exist in the database. Please try again.")
            
        # TODO: Add the conditional constraints

        for obj in spec_content["optimisation_objectives"]:
            if obj["benchmark"] != None:
                self.update_target_benchmark(obj["benchmark"], obj["metric"])
                obj_name = obj["benchmark"] + '_' + obj["metric"]
                obj_direction = obj["obj_direct"]
                range_values = obj["range"]
                output_objective[obj_name] = [obj_direction, int(range_values[0]), int(range_values[1]), obj["benchmark"]]
            else:
                obj_name = obj["metric"]
                obj_direction = obj["obj_direct"]
                range_values = obj["range"]
                output_objective[obj_name] = [obj_direction, int(range_values[0]), int(range_values[1]), 'NotBenchmark']
        target_device = spec_content["target_device"]
        fpga_info = target_fpga_info(target_device)
        resource_metrics = ["LUTs"]
        for resource_metric in resource_metrics:
            output_constraints[resource_metric] = [0, int(getattr(fpga_info, resource_metric))] 
        
        self.objective_space_info = Objective_Info(output_objective, output_constraints, optimisation_task_name)
        # Start to Fill in the constraints information
        self.param_space_info = fill_constraints(self_constraints, conditional_constraints, self.device)
        self.param_space_info.constants = input_constant
        return fpga_info



def calculate_input_dim(self_constraints):
    """this function is used to calculate the input dimension"""
    input_dim = 0
    for var_obj in self_constraints.keys():
        if self_constraints[var_obj][-1] == 'Int':
            input_dim += 1
        else:
            input_dim += len(self_constraints[var_obj][0])
    return input_dim
            

def fill_constraints(self_constraints, conditional_constraints, device):
    """this function is used to fill the constraints in the interface"""
    # Int Val: {var_name: [lower_bound, upper_bound, scale, exp, Int]}
    # Coupled_constraints: [{var_name: [lower_bound, upper_bound], var_name: [lower_bound, upper_bound]},... ]
    # Input_categorical: {var_name: [index, num_categories, categorical_vals]}
    # format_coupled_constraint : {0: [1, 4], 1: [4, 4]}
    input_dim = calculate_input_dim(self_constraints)
    input_scales = [1] * input_dim
    input_normalized_factor = [1] * input_dim
    input_offset = [0] * input_dim
    input_exp = [1] * input_dim
    input_names = list(self_constraints.keys())
    input_categorical = {}
    var_index = 0
    for var_obj in self_constraints.keys():
        if self_constraints[var_obj][-1] == 'Int':
            if self_constraints[var_obj][3] > 1:
                #has exps
                input_offset[var_index] = int(math.log(self_constraints[var_obj][0], self_constraints[var_obj][3]))
                #force the scales to be 1 if the exps is used
                self_constraints[var_obj][2] = 1
                input_normalized_factor[var_index] = int(math.log(self_constraints[var_obj][1], self_constraints[var_obj][3])) - input_offset[var_index]
                input_exp[var_index] = self_constraints[var_obj][3]
            else:
                input_scales[var_index] = int(self_constraints[var_obj][2])
                input_normalized_factor[var_index] = int((self_constraints[var_obj][1] - self_constraints[var_obj][0])/ input_scales[var_index])
                input_offset[var_index] = int(self_constraints[var_obj][0])
            var_index += 1
        else:
            input_categorical[var_obj] = [var_index, len(self_constraints[var_obj][0]), self_constraints[var_obj][0]]
            var_index += len(self_constraints[var_obj][0])
    # Build the constraints (This part of the program could be optimised further)
    constraint = Input_Constraints(input_dim, input_names, input_categorical, device)
    constraint.update_integer_transform_info(input_offset, input_scales, input_normalized_factor, input_exp)
    
    if len(conditional_constraints) != 0:
        format_coupled_constraint = []
        for or_constraint in range(len(conditional_constraints)):
            and_constraints = {}
            for and_constraint in conditional_constraints[or_constraint].keys():
                and_constraints[str(and_constraint)] = conditional_constraints[or_constraint][and_constraint]
            format_coupled_constraint.append(and_constraints)
        constraint.update_coupled_constraints(format_coupled_constraint)
    
    return Param_Space_Info(input_dim, input_scales, input_normalized_factor, input_exp, input_offset, input_names, constraint, input_categorical, self_constraints, conditional_constraints) 



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
    for classification, settings in data["Performance"].items():
        metrics = []
        for m in settings.keys():
            metrics.append(m)
        if classification == "Power":
            tmp_power = classification_metrics(metrics)
        elif classification == "Resource_Utilisation":
            tmp_resource = classification_metrics(metrics)
        elif classification == "Timing":
            tmp_timing = classification_metrics(metrics)
        elif classification == "Benchmark":
            tmp_benchmark = classification_metrics(metrics)        
    output_lib = output_params(tmp_power, tmp_resource, tmp_benchmark, tmp_timing)
    # Build CPU object
    cpu_info = object_cpu_info(data["CPU_Name"], extracted_config_params, output_lib)
    return cpu_info

if __name__ == '__main__':
    read_cpu_info_from_json('../dataset/constraints/RocketChip_Config.json')