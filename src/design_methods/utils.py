import torch
import numpy as np
import matplotlib.pyplot as plt
from botorch.utils.multi_objective.box_decompositions.non_dominated import NondominatedPartitioning
import re
import pickle
import datetime



def calculate_smooth_condition(x, condition):
    """Smooth, differentiable step function. Used for calculating the output constraints"""
    # return (1 / (1 + torch.exp(-10 * (x - condition[1]))) - 1 / (1 + torch.exp(-10 * (x - condition[0]))) + 0.5) * 1e-1
    return (1 / (1 + torch.exp(-10 * (x - condition[1])))) - 0.5

def calculate_hypervolume(ref_points, train_obj, obj_to_optimise_dim = 0):
    """Calculate the hypervolume. This is for multi-objective optimisation."""
    # Y dimension (batch_shape) x n x m-dim
    partitioning = NondominatedPartitioning(ref_point=ref_points, Y = train_obj[..., : obj_to_optimise_dim])
    hv = partitioning.compute_hypervolume().item()
    return hv

def normalise_input_data(input_tensor, normalized_factors):
    """This function is used to normalise the input data, it is not used currently"""
    num_restarts, d_dim = input_tensor.shape
    output_tensor = torch.empty((num_restarts, d_dim), dtype=input_tensor.dtype)
    for i in range(num_restarts):
        for j in range(d_dim):
            output_tensor[i][j] = input_tensor[i][j] / normalized_factors[j]
    return output_tensor

def standardize_tensor(x):
    """Standardizes a tensor of shape [n, 1] by subtracting the mean and dividing by the standard deviation."""
    mean = x.mean(dim=0, keepdim=True)  # Compute mean along the first dimension
    std = x.std(dim=0, keepdim=True)    # Compute standard deviation along the first dimension
    # Check if standard deviation is zero to avoid division by zero
    if std == 0:
        return x - mean
    else:
        return (x - mean) / std

def obtain_categorical_input_data(input_tensor, categorical_info):
    """This function is used to recover the categorical input data"""
    d_dim = input_tensor.shape[0]
    result_array = []
    start_idx = 0
    for single_categorical_info in categorical_info.values():
        idx, length = single_categorical_info[0], single_categorical_info[1]
        # add the elements before the start of the categorical data to the result array
        if idx > start_idx:
            result_array+= input_tensor[start_idx:idx].tolist()
        segment = input_tensor[idx:idx+length]
        max_index = int(torch.argmax(segment, dim=0))
        result_array.append(single_categorical_info[2][max_index])
        start_idx = idx + length
    
    # Add the remaining part of the tensor if any
    if start_idx < d_dim:
        result_array+= input_tensor[start_idx:].tolist()
    return result_array

def recover_categorical_input_data(input_tensor, categorical_info):
    """this function is used to extract the input variables that belongs to the categorical values and assign the maximum value with 1 and the rest with 0"""
    # Process each index and corresponding length
    recovered_categorical_tensor= input_tensor.clone()
    if input_tensor.dim() == 1:
        for single_categorical_info in categorical_info.values():
            idx, length = single_categorical_info[0], single_categorical_info[1]
            segment = input_tensor[idx:idx+length]
            result = torch.zeros_like(segment)
            max_value = torch.max(segment)
            result[segment == max_value] = 1
            recovered_categorical_tensor[idx:idx+length] = result
    elif input_tensor.dim() == 2:
        # W/O Batch
        for sample_num in range(input_tensor.shape[0]):
            for single_categorical_info in categorical_info.values():
                idx, length = single_categorical_info[0], single_categorical_info[1]
                segment = input_tensor[sample_num][idx:idx+length]
                result = torch.zeros_like(segment)
                max_value = torch.max(segment, dim=0)
                result[segment == max_value] = 1
                recovered_categorical_tensor[sample_num][idx:idx+length] = result
    elif input_tensor.dim() == 3:
        # With Batch
        for batch_num in range(input_tensor.shape[0]):
            for sample_num in range(input_tensor.shape[1]):
                for single_categorical_info in categorical_info.values():
                    idx, length = single_categorical_info[0], single_categorical_info[1]
                    segment = input_tensor[batch_num][sample_num][idx:idx+length]
                    result = torch.zeros_like(segment)
                    max_value = torch.max(segment, dim=0)
                    result[segment == max_value] = 1
                    recovered_categorical_tensor[batch_num][sample_num][idx:idx+length] = result
    return recovered_categorical_tensor


def recover_single_input_data(input_tensor, normalised_factor, scales, offsets, categorical_info, exps = None):
    """This function transforms the elements within the tensor individually based on the conditions."""
    # Assuming input_tensor is in the shape of num_restarts x d_dim
    # Initialize an empty tensor for the results with the same shape as input_tensor
    input_var = torch.empty_like(input_tensor)
    print("recover_single_input_data")
    if categorical_info is not None:
        # Recover the categorical data
        recovered_categorical_input_tensor = recover_categorical_input_data(input_tensor, categorical_info) 
    else:
        recovered_categorical_input_tensor = input_tensor.clone()
    
    for i in range(recovered_categorical_input_tensor.shape[0]):
        # Check if exps is not None and the element in exps is larger than one
        if exps is not None and exps[i] > 1:
            input_var[i] = exps[i] ** (torch.round(recovered_categorical_input_tensor[i] * normalised_factor[i]) * scales[i] + offsets[i])
        else:
            input_var[i] = torch.round(recovered_categorical_input_tensor[i] * normalised_factor[i]) * scales[i] + offsets[i]
    
    if categorical_info is not None:
        return obtain_categorical_input_data(input_var, categorical_info)
    else:
        return input_var.tolist()

def recover_unrounded_input_data(input_tensor, input_info, type, device):
    """This function is to find the unrounded version of the real input from the x tensor in recording process"""
    if input_info.input_exp is not None and input_info.input_exp > 1:
        results = torch.tensor(input_info.input_exp, dtype=type, device=device) ** (torch.round(input_tensor * torch.tensor(input_info.input_normalized_factor, dtype=type, device=device)) * torch.tensor(input_info.input_scales, dtype=type, device=device) + torch.tensor(input_info.input_offsets, dtype=type, device=device))
    else:
        results = input_tensor * torch.tensor(input_info.input_normalized_factor, dtype=type, device=device) * torch.tensor(input_info.input_scales, dtype=type, device=device) + torch.tensor(input_info.input_offsets, dtype=type, device=device)
    return results


def recover_output_data(input_tensor, normalized_factors):
    """This function is used to recover the output data"""
    obj_m, num_restarts = input_tensor.shape
    output_tensor = torch.empty((obj_m, num_restarts), dtype=input_tensor.dtype)
    for i in range(obj_m):
        for j in range(num_restarts):
            output_tensor[i][j] = input_tensor[i][j] * normalized_factors[i]
    return output_tensor

def encapsulate_obj_tensor_into_dict(objs, obj_tensor):
    """This function is used to facilitate the recording of the output results"""
    obj_dict = {}
    obj_index = 0
    for obj in objs.keys():
        obj_dict[obj] = obj_tensor[... , obj_index].item()
        obj_index += 1
    return obj_dict 


def extract_best_from_initialisation_results(initial_train_x, initial_obj, hypervolumes, obj_to_opt, obj_const):
    """This function is used to extract the best results from the initialisation sampling process."""
    max_value, max_index = torch.max(hypervolumes, 0)
    best_observation_per_interation = encapsulate_obj_tensor_into_dict(obj_to_opt, initial_obj[max_index.item()])
    best_constraint_per_interation = encapsulate_obj_tensor_into_dict(obj_const, initial_obj[max_index.item(), len(obj_to_opt):])
    best_hyper_vol_per_interation = max_value
    best_sample_point_per_interation = initial_train_x[max_index.item()].unsqueeze(0)
    return best_sample_point_per_interation, best_observation_per_interation, best_constraint_per_interation, best_hyper_vol_per_interation


def find_ref_points(OBJECTIVES_DIM, OBJECTIVES, t_type, device):
    """This function is used to find the reference points for qNEHVI optimisation"""
    # Assuming that all the objectives are normalised.
    ref_points = torch.empty((OBJECTIVES_DIM), device=device, dtype=t_type)
    ref_point_index = 0
    for obj in OBJECTIVES.keys():
        if(OBJECTIVES[obj] == 'minimise'):
            ref_points[ref_point_index] = -1
        else:
            ref_points[ref_point_index] = 1
        ref_point_index += 1
    return ref_points

def calculate_volumes_for_brute_force(objs, normalised_factors, objs_to_optimise_dim):
    """This function is used for brute force optimisation to calculate the volume of the design space"""
    volumes = 1
    for obj_index in range(objs_to_optimise_dim):
        volumes *= objs[obj_index]/ normalised_factors[obj_index]
    return volumes


def find_max_index_in_list(list):
    max_index = 0
    for i in range(len(list)):
        if(list[i] > list[max_index]):
            max_index = i
    return max_index



def read_utilization(rpt_file_path, variable_names):
    """This function is used to read the utilization from the Vivado report file"""
    in_section = False
    # Define a pattern to match the rows in the utilization table
    row_pattern = re.compile(r'\|\s*(.*?)\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+\.\d+|\d+)\s*\|')

    # Initialize a list to hold multiple matches, if any
    results = []

    try:
        with open(rpt_file_path, 'r') as file:
            table_margin_count = 0
            for line in file:
                # Check if we've reached the CLB Logic section, only focus on this section first.
                if 'CLB Logic' in line:
                    in_section = True
                # Check if we've passed the section of interest
                elif in_section and '+----------------------------+' in line:
                    table_margin_count += 1  # Exit the loop if we're past the relevant section
                elif in_section:
                    # Match the row pattern within the section
                    match = row_pattern.match(line)
                    for variable_name in variable_names:
                        if match and variable_name in match.group(1):
                            # Append the variable name and its Util% to the results list
                            results.append(float(match.group(2)))
                if table_margin_count == 3:
                    break
            return results
    except FileNotFoundError:
        print(f"File not found: {rpt_file_path}")
        return

def extract_worst_slack(file_path):
    # Define regex patterns to match the lines with worst slack values
    setup_pattern = r"Setup\s*:\s*\d+\s*Failing Endpoints,\s*Worst Slack\s*([-+]?\d*\.?\d+ns)"
    hold_pattern = r"Hold\s*:\s*\d+\s*Failing Endpoints,\s*Worst Slack\s*([-+]?\d*\.?\d+ns)"
    
    setup_worst_slack = None
    hold_worst_slack = None
    
    # Read the file and search for the patterns
    with open(file_path, 'r') as file:
        for line in file:
            if not setup_worst_slack:
                setup_match = re.search(setup_pattern, line)
                if setup_match:
                    setup_worst_slack = setup_match.group(1)
                    
            if not hold_worst_slack:
                hold_match = re.search(hold_pattern, line)
                if hold_match:
                    hold_worst_slack = hold_match.group(1)
                    
            # If both values are found, no need to continue reading
            if setup_worst_slack and hold_worst_slack:
                break
    setup_result = float(setup_worst_slack.split('ns')[0])
    hold_result = float(hold_worst_slack.split('ns')[0])
    return setup_result, hold_result

def find_the_anticipated_fastest_time_period(file_path, default_max_freq):
    # TODO Here
    """This function is used to find the anticipated maximum frequency"""
    setup_slack, hold_slack = extract_worst_slack(file_path)
    # Find the minimum slack value
    min_slack = min(setup_slack, hold_slack)
    # Calculate the anticipated maximum frequency
    anticipated_fastest_time_period = (1/default_max_freq - min_slack)
    return anticipated_fastest_time_period


def save_data_to_file(filename, data):
    with open(filename, 'wb') as f:
        pickle.dump(data, f)


def get_device():
    # Checks if a GPU is available and returns it as the device, otherwise returns the CPU.
    if torch.cuda.is_available():
        # If a GPU is available, it sets the device to GPU (cuda)
        return torch.device("cuda")
    else:
        # If no GPU is available, it sets the device to CPU
        return torch.device("cpu")

def get_tensor_type():
    return torch.float64

#<--------------------------------- Classes for recording the results --------------------------------->

class recorded_training_result:
    """This class is used to record the results of optimisation."""
    def __init__(self, input_names, objectives, record_file_dir, num_trials, num_iterations):
        self.objs  = objectives
        self.history = {}
        self.iterations = num_iterations
        self.trials = num_trials
        now = datetime.datetime.now()
        # Format the date and time in the desired format (year_month_day_hour_minute)
        filename = now.strftime('%Y_%m_%d_%H_%M')
        self.record_file_name = record_file_dir + filename

        for i in range(num_trials * num_iterations):
            self.history[i] = {}
        self.input_history = {}
        self.input_names = input_names

    def record(self, iteration, trial, best_objs, best_hypervol, time):
        self.history[(trial -1) * self.iterations + (iteration-1)] = [best_objs, best_hypervol, time]
    
    def record_and_write(self, iteration, trial, best_objs, best_hypervol, time):
        self.history[(trial -1) * self.iterations + (iteration-1)] = [best_objs, best_hypervol, time]
        with open(self.record_file_name + '_BO.txt', 'a') as f:
            f.write(f"{(trial -1) * self.iterations + (iteration-1)}, {time:>4.2f}")
            f.write(f", {best_hypervol}")
            for obj in self.objs:
                result = best_objs.get(obj, 0)
                f.write(f", {result}")
            f.write("\n")
    
    def store(self):
        total_time = 0
        with open(self.record_file_name + '_BO.txt', 'w') as f:
            f.write("iteration, time, hyper_vol")
            for obj in self.objs:
                f.write(f", {obj}")
            f.write("\n")
            for i in range(self.trials * self.iterations):
                total_time += self.history[i][2]
                f.write(f"{i}, {total_time:>4.2f}")
                f.write(f", {self.history[i][1]}")
                for obj in self.objs:
                    result = self.history[i][0].get(obj, 0)
                    f.write(f", {result}")
                f.write("\n")
        
        # with open(self.record_file_name + 'record_input.txt', 'w') as f:
        #     f.write("trial, hyper_vol")
        #     for name in self.input_names:
        #         f.write(f", {name}")
        #     f.write("\n")
        #     for trial in self.input_history.keys():
        #         for data_idx in range(len(self.input_history[trial][1])):
        #             f.write(f"{trial}, {self.input_history[trial][2][data_idx]}")
        #             for input_index in range(len(self.input_names)):
        #                f.write(f", {self.input_history[trial][1][data_idx][input_index]}")
        #             f.write("\n")
    

class other_model_training_result:
    """This class is used to record the results of brute force optimisation."""
    def __init__(self, input_vars, objectives, overall_iteration_size, record_file_name):
        self.history = {}
        self.input_vars = input_vars
        self.objs  = objectives
        self.record_file_name = record_file_name
        self.train_set_size = 0
        for i in range(overall_iteration_size):
            self.history[i] = {}

    def record(self, iteration, sample_input, sample_volume, best_objs, time):
        self.history[iteration] = [sample_input, sample_volume, best_objs, time]
        self.train_set_size = iteration + 1
    
    def store(self):
        total_time = 0
        with open(self.record_file_name, 'w') as f:
            f.write("iteration, time")
            for input in self.input_vars:
                f.write(f", {input}")
            f.write(", current_hyper_vol")
            for obj in self.objs:
                f.write(f", {obj}")
            f.write("\n")
            for i in range(self.train_set_size):
                valid_history = self.history.get(i, None)
                if(valid_history != {} and valid_history != None):
                    total_time += valid_history[3]
                    f.write(f"{i}, {total_time:>4.2f}")
                    for input in valid_history[0]:
                        f.write(f", {input.item()}")
                    f.write(f", {valid_history[1]}")
                    for obj in self.objs:
                        result = valid_history[2][obj]
                        f.write(f", {result}")
                    f.write("\n")


class test_posterior_result:
    """This class is used to visualise the posterior funcitons"""
    def __init__(self, input_names, dtype, device, num_samples = 100):
        self.dim = len(input_names)
        self.input_names = input_names
        self.X = np.linspace(0, 1, num_samples) 
        self.num_samples = num_samples
        self.save_directory= '../test/Model_Test_Results/'
        # Create multi-dimensional grids
        basis_grid = np.meshgrid(*[self.X for _ in range(self.dim)])
        # Flatten and combine all grids to form the combination array
        # Each row in the combination array represents a point in the multi-dimensional space
        combination_array = np.vstack([grid.ravel() for grid in basis_grid]).T
        # Convert the combination array to a PyTorch tensor
        self.testcase = torch.from_numpy(combination_array).to(dtype=dtype, device=device)

    def examine_posterior(self, model, iteration):
        """This function is used to examine the function"""
        # self.mean_prediction, self.std_deviation = model.forward(self.testcase)
        posterior = model.posterior(self.testcase)
        mean_prediction = posterior.mean.cpu().detach().numpy()  # Mean of the predictive distribution
        std_deviation = posterior.variance.cpu().detach().numpy() 

        Z_mean = mean_prediction.reshape([self.num_samples for _ in range(self.dim)])
        Z_uncertainty = std_deviation.reshape([self.num_samples for _ in range(self.dim)])

        X = self.testcase[:,0].cpu().detach().numpy().reshape([self.num_samples for _ in range(self.dim)])
        Y = self.testcase[:,1].cpu().detach().numpy().reshape([self.num_samples for _ in range(self.dim)])
        data = {
            'Z_mean': Z_mean,
            'Z_uncertainty': Z_uncertainty,
            'X': X,
            'Y': Y
        }
        save_data_to_file(self.save_directory + 'posterior.pkl', data)


        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        # surf = ax.plot_surface(X, Y, Z_mean, cmap='viridis', edgecolor='none', alpha=0.7)
        # # Plot Uncertainty using Contourf  at the base
        # min_uncertainty, max_uncertainty = np.min(Z_uncertainty), np.max(Z_uncertainty)
        # levels  = np.linspace(min_uncertainty, max_uncertainty, num=10)
        # levels  = np.unique(levels)  # Ensure levels are unique
        # epsilon = np.diff(levels).min() * 0.1  # Small increment
        # levels[1:] += epsilon  # Avoid incrementing the first level to keep the minimum

        # contour = ax.contourf(X, Y, Z_uncertainty, zdir='z', offset=Z_mean.min()-0.25, levels=levels, cmap='inferno', alpha=0.5)

        # ax.set_xlabel(self.input_names[0])
        # ax.set_ylabel(self.input_names[1])
        # # ax.set_zlabel('Mean Prediction')
        # ax.set_title('Posterior Mean and Uncertainty at Iteration ' + str(iteration))

        # # Add a color bar for the contour plot
        # cbar = fig.colorbar(contour, shrink=0.5, aspect=5, label='Uncertainty (Std Dev)', orientation='horizontal')
        # cbar.ax.xaxis.set_ticks_position('bottom')
        # cbar.ax.xaxis.set_label_position('bottom')
        # cbar.ax.set_anchor((0.5, -0.15))
        # plt.show()

    def examine_acq_function(self, acq_function, iteration):
        """This function is used to examine the acquisition function"""
        acq_values = acq_function(self.testcase.unsqueeze(-2)).cpu().detach().numpy()
        Z = acq_values.reshape([self.num_samples for _ in range(self.dim)])
        X = self.testcase[:,0].cpu().detach().numpy().reshape([self.num_samples for _ in range(self.dim)])
        Y = self.testcase[:,1].cpu().detach().numpy().reshape([self.num_samples for _ in range(self.dim)])
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.7)
        ax.set_xlabel(self.input_names[0])
        ax.set_ylabel(self.input_names[1])
        ax.set_zlabel('Acquisition Function Value')
        ax.set_title('Acquisition Function Examination at Iteration ' + str(iteration))
        plt.savefig('acquisition_function.png')
        

        



if __name__ == '__main__':
    # print("test")
    # result = read_utilization('D:\\Imperial\\Year4\\MasterThesis\\FYP_Bayesian_Optimisation\\object_functions\\Syn_Report\\NutShell_utilization_synth.rpt', ['LUT as Logic', 'CLB Registers'] )
    # print(result)
    # x_values = torch.linspace(-0, 0.5, 1000)
    # # Define the condition (start and end points of the step)
    # condition = [0, 0.03]  # Example condition
    # # Calculate y values using the smooth condition function
    # y_values = calculate_smooth_condition(x_values, condition)
    # print(y_values)
    # test = read_utilization('../object_functions/Syn_Report/EL2_utilization_synth.rpt', ['LUT as Logic', 'CLB Registers'])
    # print(test)
    test = extract_worst_slack('../object_functions/Syn_Report/rocket_time_summary.rpt')
    print(test)

    
