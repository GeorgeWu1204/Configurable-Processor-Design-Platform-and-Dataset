import os.path as osp
import os
import json
import numpy as np
import subprocess


class match_metrics:
    #TODO Improve better metric for matching configurations, perhaps including some weights.
    def __init__(self, match_metric, weights):
        self.metrics = ['euclidean', 'manhattan_distance']
        self.param_weights = np.array(list(weights.values()))
        if match_metric not in self.metrics:
            raise ValueError(f"Invalid metric: {match_metric}. Must be one of {self.metrics}")
        else:
            self.match_metric = match_metric
    
    def euclidean_distance(self, config1, config2):
        return float(np.sum(np.multiply(np.sqrt((config1 - config2) ** 2 ), self.param_weights)))
    
    def manhattan_distance(self, config1, config2):
        return float(np.sum(np.multiply(np.abs(config1 - config2), self.param_weights )))

    def calculate_distance(self, config1, config2):
        if self.match_metric == 'euclidean':
            return self.euclidean_distance(np.log2(config1), np.log2(config2))
        elif self.match_metric == 'manhattan_distance':
            return self.manhattan_distance(np.log2(config1), np.log2(config2))
        else:
            raise ValueError(f"Invalid metric: {self.match_metric}. Must be one of {self.metrics}")
        

class config_matcher:
    def __init__(self, cpu_info, check_point_to_synthesis_name, match_metric='euclidean'):
        self.cpu_info = cpu_info
        self.synthesis_checkpoint_directory = f'../processors/checkpoints/{self.cpu_info.cpu_name}/Synthesis/'
        self.synthesis_checkpoint_record_history = f'../processors/checkpoints/{self.cpu_info.cpu_name}/Stored_Checkpoint_Record.json'
        self.match_metric = match_metric
        self.metric_calculator = match_metrics(self.match_metric, self.cpu_info.config_params.params_weights)
        self.check_point_to_synthesis_name = check_point_to_synthesis_name
    
    def load_json(self):
        try:
            with open(self.synthesis_checkpoint_record_history, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f'File {self.synthesis_checkpoint_record_history} does not exist or is empty')
            return {}  # Return an empty dict if the file does not exist

    def store_checkpoint(self, config_under_evaluation):
        if not osp.exists(self.synthesis_checkpoint_directory):
            os.makedirs(self.synthesis_checkpoint_directory)

        format_config = {}
        for i, param in enumerate(self.cpu_info.config_params.params):
            format_config[param.name] = int(config_under_evaluation[i])
        
        stored_configs = self.load_json()
        lastest_config_index = -1
        for key in stored_configs.keys():
            index = int(key.split('_')[-1])
            if stored_configs[key] == format_config:
                print(f'Config already stored in index {index}')
                return
            if index > lastest_config_index:
                lastest_config_index = index
        
        current_config_index = lastest_config_index + 1
        config_key = f'config_{current_config_index}'
        stored_configs[config_key] = format_config
        with open(self.synthesis_checkpoint_record_history, 'w') as f:
            json.dump(stored_configs, f, indent=4)
            f.write('\n')
        self.rename_and_store_checkpoint(config_key)
    
    def prepare_checkpoint(self, checkpoint_config_index):
        if checkpoint_config_index is None:
            print("No checkpoint index provided.")
            return False
        else:
            try:
                # Use subprocess to execute the copy command with rename
                subprocess.run(
                    ['cp', '-f', f'{self.synthesis_checkpoint_directory}{checkpoint_config_index}.dcp', f'{self.synthesis_checkpoint_directory}{self.check_point_to_synthesis_name}.dcp'],
                    check=True  # Raises an error if the command fails
                )
                return True
            except subprocess.CalledProcessError as e:
                Exception(f"Error: {e}")
                return False


    def rename_and_store_checkpoint(self, new_checkpoint_name):
        try:
            # Use subprocess to execute the copy command with rename
            subprocess.run(
                ['mv', f'{self.synthesis_checkpoint_directory}{self.check_point_to_synthesis_name}.dcp', f'{self.synthesis_checkpoint_directory}{new_checkpoint_name}.dcp'],
                check=True  # Raises an error if the command fails
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return False
    

    def match_config(self, config_to_evaluate):
        stored_configs = self.load_json()
        min_distance = float('inf')
        best_config_name = 'config_0'
        for key in stored_configs.keys():
            stored_config = stored_configs[key]
            stored_config = np.array([stored_config[param.name] for param in self.cpu_info.config_params.params])
            distance = self.metric_calculator.calculate_distance(stored_config, config_to_evaluate)
            if distance < min_distance:
                print(f'New best distance: {distance}')
                min_distance = distance
                best_config_name = key
        return best_config_name



def analyse_config_weights_for_synthesis(dataset):
    default_config = dataset.default_params
    print("Default Config", default_config)
    #Test
    dataset.tuner.build_new_processor(default_config)


    _, _, _, default_rc = dataset.fetch_single_data_acc_to_def_from_dataset(default_config)
    print("Default Utilisation Results", default_rc)
    weight = [0 for _ in range(len(default_config))]
    previous_param_name = None
    for param in dataset.cpu_info.config_params.params:
        print(f"Analyzing config: {param.name}")
        config_to_test = default_config.copy()
        # Check if involved in conditional constraints
        # here we assume the nSets and nWays are close to each other in config_params
        if previous_param_name != None and previous_param_name.split('_')[0] == param.name.split('_')[0] and (previous_param_name.split('_')[1] == "nSets" or previous_param_name.split('_')[1] == "nTLBSets"):
            # if changing the nSets, we should ignore nWays, as the size of the cache is depend on nSets * nWays
            previous_param_name = param.name
            continue
        previous_param_name = param.name
        rc_weights = []
        for i in [-1,1]:
            index_of_value = param.self_range.index(default_config[param.index]) + i
            if index_of_value >= len(param.self_range) or index_of_value < 0:
                continue
            modified_param_val = param.self_range[index_of_value]
            config_to_test[param.index] = int(modified_param_val)
            print(f"Testing config: {config_to_test}")
            dataset.tuner.build_new_processor(config_to_test)
            dataset.tuner.run_synthesis(config_to_test)
            parsed_rc_results = dataset.tuner.parse_vivado_resource_utilisation_report()
            print(parsed_rc_results)
            rc_weights.append(calculate_weight(default_rc, list(parsed_rc_results.values())))
            print("Utilisation Results")
            print(rc_weights)
        weight[param.index] = sum(rc_weights) / len(rc_weights)
        print("weight   ", weight[param.index])
    return weight
        

def calculate_weight(ref_rc_results, new_rc_results):
    # Note: This weight assumes the configuration parameters are converted to log.
    if len(ref_rc_results) != len(new_rc_results):
        raise ValueError("Resource utilisation results must have the same dimensions.")
    ref_rc_results = np.array(ref_rc_results, dtype=float)
    new_rc_results = np.array(new_rc_results, dtype=float)
    result = np.sum(((ref_rc_results - new_rc_results) ** 2) / (ref_rc_results ** 2))
    return result

if __name__ == '__main__':
    from interface import define_cpu_settings
    cpu_info, fpga_info = define_cpu_settings()
    matcher = config_matcher(cpu_info, "ChipTop")
    matcher.prepare_checkpoint("config_1")