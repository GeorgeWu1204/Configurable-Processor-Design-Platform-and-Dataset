
from design_methods.format_constraints import Input_Constraints
import math
import json
import os.path as osp


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