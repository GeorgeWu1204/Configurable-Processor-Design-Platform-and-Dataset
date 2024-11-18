import ast
import torch
import glob
import sys
import pickle
import os.path as osp
from design_methods.utils import calculate_smooth_condition, recover_single_input_data, read_utilization, find_the_anticipated_fastest_time_period
from botorch.utils.transforms import normalize

def build_processor_analyser(param_space_info, objective_space_info, processor_dataset, t_type, device):
    if processor_dataset.cpu_info.cpu_name == 'RocketChip':
        return RocketChip_Analyser(param_space_info, objective_space_info, processor_dataset, t_type, device)
    elif processor_dataset.cpu_info.cpu_name == 'EL2':
        return EL2_Analyser(param_space_info, objective_space_info, processor_dataset, t_type, device)
    elif processor_dataset.cpu_info.cpu_name == 'BOOM':
        return Processor_Analyser(param_space_info, objective_space_info, processor_dataset, t_type, device)
    

def read_data_from_db(db_name):
    db = {}
    if not osp.exists(db_name):
        print(f"[i] generating: '{db_name}'")
        if len(sys.argv) == 2:
            loc = sys.argv[1]
        else:
            loc = "**"

        for dbf in glob.glob(f'{loc}/ppa*.db', recursive=True):
            print(f"[i] loading db: '{dbf}'")
            with open(dbf, 'r') as f:
                local_db = eval(f.read())
                db.update(local_db)

        # pickle our database
        with open(db_name, 'wb') as f:
            pickle.dump(db, f)
    else:
        print(f"[i] loading: '{db_name}'")
        with open(db_name, 'rb') as f:
            db.update(pickle.load(f))
    return db


class Data_Sample:
    """Individual Storage Element"""
    def __init__(self, data, objs, data_set_type):
        self.objective_vals = {}
        if (data_set_type == 'txt'):
            for obj in objs:
                if obj == 'ncycle_2':
                    index = obj.split('_')[-1]
                    self.objective_vals[obj] = int(list(data[1][int(index)].values())[0])
                else:
                    self.objective_vals[obj] = data[2][obj]
        elif (data_set_type == 'db'):
            self.Constraints = data[0]
            self.Cycle_count = None
            for obj in objs:
                self.objective_vals[obj] = data[1][obj]
    def get_objectives(self, obj):
        return self.objective_vals.get(obj, None)

class Processor_Analyser:
    """This class is used for DSE where the dataset is provided"""
    def __init__(self, param_space_info, objective_space_info, data_set_type = 'txt', tensor_type = torch.float64, tensor_device = torch.device('cpu')):
        val_list = {}
        self.best_value = {}
        self.best_pair = {}
        self.worst_value = {}
        # to recover the output data
        self.objs_to_optimise_dim = objective_space_info.obj_to_optimise_dim
        self.objs_to_evaluate = list(objective_space_info.obj_to_optimise.keys()) + list(objective_space_info.output_constraints.keys())
        self.objs_to_evaluate_dim = len(self.objs_to_evaluate)
        self.output_normalised_factors = {}
        self.objs_direct = {}    
        # to recover the input data
        self.input_normalized_factors = torch.tensor(param_space_info.input_normalized_factor, dtype=tensor_type, device=tensor_device)
        self.input_scales_factors = torch.tensor(param_space_info.input_scales, dtype=tensor_type, device=tensor_device)
        self.input_offsets = torch.tensor(param_space_info.input_offsets, dtype=tensor_type, device=tensor_device)
        self.input_exp = torch.tensor(param_space_info.input_exp, dtype=tensor_type, device=tensor_device)
        self.input_constants = param_space_info.constants
        self.input_categorical = param_space_info.input_categorical
        # tensor type and device
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
        self.normaliser_bounds = torch.empty((2, self.objs_to_evaluate_dim), dtype=tensor_type, device=tensor_device)
        
        if data_set_type == 'txt':
            file_name = '../specification/Simple_Dataset/ppa.txt'
            with open(file_name, 'r') as f:
                content = f.read()
                raw_data = ast.literal_eval(content)
            for i in range(len(raw_data)):
                d_input_dic = raw_data[i][0]
                d_input = [val for val in d_input_dic.values()]
                self.__dict__[tuple(d_input)] = Data_Sample(raw_data[i], self.objs_to_evaluate, data_set_type)
        elif data_set_type == 'db':
            for obj in self.objs_to_evaluate:
                val_list[obj] = []
            raw_data = read_data_from_db('../specification/Simple_Dataset/ppa_v2.db')
            for i in raw_data.keys():
                self.__dict__[i] = Data_Sample([i, raw_data[i]], self.objs_to_evaluate, data_set_type)
                for obj in self.objs_to_evaluate:
                    val_list[obj].append(raw_data[i][obj])
            

            # Iterate over each item in output_objective
        obj_index = 0
        for obj, values in objective_space_info.obj_to_optimise.items():
            # Extract the obj_direction from the values list
            obj_direction = values[0]
            self.objs_direct[obj] = obj_direction
            if obj_direction == 'minimise':
                self.best_value[obj] = values[1]
                self.worst_value[obj] = values[2]
                self.normaliser_bounds[0][obj_index] = -1 * values[1]
                self.normaliser_bounds[1][obj_index] = -1 * values[2]
            else:
                self.best_value[obj] = values[2]
                self.worst_value[obj] = values[1]
                self.normaliser_bounds[0][obj_index] = values[1]
                self.normaliser_bounds[1][obj_index] = values[2]
            # for recording the best pair
            # self.normaliser_bounds[0][obj_index] = min()
            # self.normaliser_bounds[1][obj_index] = max(val_list[obj])
            # self.best_pair[obj] = [[i] for i in raw_data.keys() if raw_data[i][obj] == self.best_value[obj]][0]
            obj_index += 1
        self.output_constraints_to_check = []
        for obj in objective_space_info.output_constraints:
            self.best_value[obj] = objective_space_info.output_constraints[obj][1]
            self.worst_value[obj] = 0.0
            self.output_constraints_to_check.append([self.normalise_single_output_data(bound,obj) for bound in objective_space_info.output_constraints[obj]])
            self.normaliser_bounds[0][obj_index] = objective_space_info.output_constraints[obj][0]
            self.normaliser_bounds[1][obj_index] = objective_space_info.output_constraints[obj][1]

    def normalise_output_data_tensor(self, input_tensor):
        """This function is used to normalise the output data in tensor format"""
        sign_tensor = torch.sign(input_tensor)
        normalised_result = normalize(input_tensor, self.normaliser_bounds)
        return normalised_result * sign_tensor
    
    def normalise_single_output_data(self, input_data, obj):
        """This function is used to normalise the output data in single data format"""
        result = (input_data - min(self.best_value[obj], self.worst_value[obj])) / abs(self.best_value[obj] - self.worst_value[obj])
        return result
    
    def format_and_add_const_to_data(self, input_data):
        """This function is used to add constant input to the input data to make it able to find the ppa result"""
        for index in self.input_constants.keys():
            input_data.insert(index, self.input_constants[index])
        return tuple(input_data)
    
    def find_evaluation_results(self, sample_inputs):
        """Find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        num_restart= sample_inputs.shape[0]
        results = torch.empty((num_restart, len(self.objs_to_evaluate)), device=sample_inputs.device, dtype=sample_inputs.dtype)
        obj_index = 0
        for i in range(num_restart):
            input = recover_single_input_data(sample_inputs[i,:], self.input_normalized_factors, self.input_scales_factors, self.input_offsets, self.input_categorical)
            sample_input = self.format_and_add_const_to_data(input)
            for obj_index in range(self.objs_to_evaluate_dim):
                obj = self.objs_to_evaluate[obj_index]
                sample_objective = self.__dict__.get(sample_input, None)
                if sample_objective is None:
                    return False, results   
                results[i][obj_index] = sample_objective.get_objectives(obj)
                if self.objs_direct.get(obj, None) == 'minimise':
                    results[i][obj_index] = -1 * results[i][obj_index]
                obj_index += 1
        return True, results

    def find_single_ppa_result_for_unnormalised_sample(self, sample_input):
        """This function is used to find the ppa result for a single input, only used in result recording"""
        formatted_input = self.format_and_add_const_to_data(sample_input)
        result = []
        for  obj in self.objs_to_evaluate:
            result.append(self.__dict__.get(tuple(formatted_input)).get_objectives(obj))
        return result

    def check_obj_constraints(self, X):
        """This is the callable function for the output constraints of the qNEHVI acq function"""
        # X shape n x m , Output shape n x 1
        # Negative implies feasible
        results = torch.zeros((X.shape[0], 1), device=X.device, dtype=X.dtype)
        for i in range(X.shape[0]):
            condition_vals = []
            for obj_index in range(self.objs_to_optimise_dim, X.shape[1]):
                condition_val = calculate_smooth_condition(X[i][obj_index], self.output_constraints_to_check[obj_index - self.objs_to_optimise_dim])
                condition_vals.append(condition_val)
            results[i] = max(condition_vals)
        return results



class EL2_Analyser(Processor_Analyser):
    def __init__(self, param_space_info, objective_space_info, processor_dataset, tensor_type=torch.float64, tensor_device=torch.device('cpu')):
        # Linked to the processor dataset.
        self.proc_dataset = processor_dataset
        # to recover the Output data
        self.objs_to_optimise_dim = objective_space_info.obj_to_optimise_dim
        self.objs_to_evaluate = list(objective_space_info.obj_to_optimise.keys()) + list(objective_space_info.output_constraints.keys())
        self.objs_to_evaluate_dim = len(self.objs_to_evaluate)
        # this is to check what type of performance objectives are needed to be stored
        self.performance_objs_benchmarks = []
        # assume all the output is percentage
        self.worst_value = {}
        self.best_value = {}
        self.objs_direct = {}
        self.normaliser_bounds = torch.empty((2, self.objs_to_evaluate_dim), dtype=tensor_type, device=tensor_device)

        # Iterate over each item in output_objective
        obj_index = 0   
        for obj_name, values in objective_space_info.obj_to_optimise.items():
            # Extract the obj_direction from the values list
            obj_direction = values[0]
            self.objs_direct[obj_name] = obj_direction
            if obj_direction == 'minimise':
                self.best_value[obj_name] = values[1]
                self.worst_value[obj_name] = values[2]
                self.normaliser_bounds[0][obj_index] = -1 * values[1]
                self.normaliser_bounds[1][obj_index] = -1 * values[2]
            else:
                self.best_value[obj_name] = values[2]
                self.worst_value[obj_name] = values[1]
                self.normaliser_bounds[0][obj_index] = values[1]
                self.normaliser_bounds[1][obj_index] = values[2]

            if values[3] != 'NotBenchmark':
                self.performance_objs_benchmarks.append(values[3])
            obj_index += 1
        
        # TODO, since for some of the conditions that are very small, the boundary calculation methods does not work well, hence normalising to the largest value of the condition.
        self.output_constraints_to_check = []
        for obj_name in list(objective_space_info.output_constraints.keys()):
            self.best_value[obj_name] = objective_space_info.output_constraints[obj_name][1]
            self.worst_value[obj_name] = objective_space_info.output_constraints[obj_name][0]
            self.output_constraints_to_check.append([self.normalise_single_output_data(bound, obj_name) for bound in objective_space_info.output_constraints[obj_name]])
            self.normaliser_bounds[0][obj_index] = objective_space_info.output_constraints[obj_name][0]
            self.normaliser_bounds[1][obj_index] = objective_space_info.output_constraints[obj_name][1]
        
        # to recover the Input data
        self.input_normalized_factors = torch.tensor(param_space_info.input_normalized_factor, dtype=tensor_type, device=tensor_device)
        self.input_scales_factors = torch.tensor(param_space_info.input_scales, dtype=tensor_type, device=tensor_device)
        self.input_offsets = torch.tensor(param_space_info.input_offsets, dtype=tensor_type, device=tensor_device)
        self.input_exp = torch.tensor(param_space_info.input_exp, dtype=tensor_type, device=tensor_device)
        self.input_constants = param_space_info.constants
        self.input_categorical = param_space_info.input_categorical

        # tensor type and device
        self.tensor_type = tensor_type
        self.tensor_device = tensor_device
    
    def find_evaluation_results(self, sample_inputs):
        """Find the ppa result for given data input, if the objective is to find the minimal value, return the negative value"""
        num_restart= sample_inputs.shape[0]
        results = torch.empty((num_restart, len(self.objs_to_evaluate)), device=sample_inputs.device, dtype=sample_inputs.dtype)
        obj_index = 0
        for i in range(num_restart):
            # num_restart needs to be fixed to 1
            input = recover_single_input_data(sample_inputs[i,:], self.input_normalized_factors, self.input_scales_factors, self.input_offsets, self.input_categorical, self.input_exp)
            sample_input = self.format_and_add_const_to_data(input)
            validity, fpga_deployibility, objective_results, rc_utilisation =  self.proc_dataset.query_dataset(sample_input)

            for obj_index in range(self.objs_to_optimise_dim):
                obj = self.objs_to_evaluate[obj_index]
                results[i][obj_index] = objective_results[obj_index]
                if self.objs_direct.get(obj, None) == 'minimise':
                    results[i][obj_index] = -1 * results[i][obj_index]
                obj_index += 1
            # add the rc utilisation to the results
            for rc_index in range(self.objs_to_optimise_dim, self.objs_to_evaluate_dim):
                obj = self.objs_to_evaluate[rc_index]
                results[i][rc_index] = rc_utilisation[rc_index - self.objs_to_optimise_dim]

            if validity == False:
                return False, results

        return True, results

    def find_all_possible_designs(self):
        """This function is used to find all the possible designs"""
        print("normalised_Factors", self.input_normalized_factors)
        ranges = [torch.linspace(0, 1, steps=int(factor) * 2 + 1, device=self.tensor_device) for factor in self.input_normalized_factors]
        # Generate all combinations using torch.meshgrid with the 'indexing' argument for future compatibility
        grids = torch.meshgrid(*ranges, indexing='ij')
        # Stack the grids to form a tensor of shape (5*3*2*3, 4)
        combinations = torch.stack(grids, dim=-1).reshape(-1, self.input_normalized_factors.size(0))
        # Use .to() method to ensure the tensor is on the right device and has the right dtype
        combinations = combinations.to(device=self.tensor_device, dtype=self.tensor_type)
        return combinations

    def brute_design_space_exploration(self):
        combinations = self.find_all_possible_designs()
        for index in range(combinations.shape[0]):
            print("combinations[index]: ", combinations[index])
            valid, result = self.find_evaluation_results(combinations[index].unsqueeze(0))
            print("valid: ", valid, "result: ", result)


class RocketChip_Analyser(EL2_Analyser):
    def __init__(self, param_space_info, objective_space_info, optimisation_task_name, tensor_type=torch.float64, tensor_device=torch.device('cpu')):
        super().__init__(param_space_info, objective_space_info, optimisation_task_name, tensor_type, tensor_device)

