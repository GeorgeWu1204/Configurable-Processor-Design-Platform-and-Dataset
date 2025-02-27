import torch
import design_methods.processor_analyser as processor_analyser
import definitions

from interface import parse_proc_spec
from format_constraints import Simpler_Constraints
from design_methods.BO.optimisation_models import brute_force, hill_climbing, genetic_algorithm

# Tensor Settings
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
t_type = torch.float64

# Input Settings
CONSTRAINT_FILE = '../specification/input_spec_optimisation_set_4.txt'
input_info, output_info, param_tuner, optimisation_name = parse_proc_spec(CONSTRAINT_FILE, device)
# Dataset Settings
if output_info.optimisation_target == 'synthetic':
    RAW_DATA_FILE = '../specification/ppa_v2.db'
    data_set = processor_analyser.read_data_from_db(RAW_DATA_FILE, input_info, output_info, t_type, device)
elif output_info.optimisation_target == 'NutShell':
    data_set = processor_analyser.NutShell_Data(input_info, output_info, param_tuner, t_type, device)
elif output_info.optimisation_target == 'EL2':
    data_set = processor_analyser.EL2_Data(input_info, output_info, param_tuner, optimisation_name, t_type, device)


print("<-------------- Optimisation Settings -------------->")
print(f"Input Names: {input_info.input_names}")
print(f"Input Self Constraints: {input_info.self_constraints}")
print(f"Input Offset: {input_info.input_offsets}")
print(f"Input Scales: {input_info.input_scales}")
print(f"Input Normalised Factor: {input_info.input_normalized_factor}")
print(f"Input Exponential: {input_info.input_exp}")
print(f"Optimisation Device : {output_info.optimisation_target}")
print(f"Objectives to Optimise: {output_info.obj_to_optimise}")
print(f"Output Objective Constraint: {output_info.output_constraints}")
print("<--------------------------------------------------->")

#Building simpler constraints
ref_points = definitions.find_ref_points(output_info.obj_to_optimise_dim, data_set.objs_direct, t_type, device)
verbose = True
record = True
record_file_name = '../test/test_results/'
#TODO: Temporarily modified for paper
obj_index = 0

# Optimisation Loop
# brute_force(input_info, output_info, ref_points, data_set, record, record_file_name)
hill_climbing(input_info, output_info, ref_points, data_set, record, record_file_name, obj_index, max_iterations=30, step_size=0.01)
# genetic_algorithm(input_info, output_info, ref_points, data_set, record, record_file_name)


