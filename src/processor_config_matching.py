import os.path as osp
import os
import json
import numpy as np
import subprocess


class match_metrics:
    #TODO Improve better metric for matching configurations, perhaps including some weights.
    def __init__(self, match_metric):
        self.metrics = ['euclidean', 'manhattan_distance']
        if match_metric not in self.metrics:
            raise ValueError(f"Invalid metric: {match_metric}. Must be one of {self.metrics}")
        else:
            self.match_metric = match_metric
    
    def euclidean_distance(self, config1, config2):
        return float(np.sqrt(np.sum((config1 - config2) ** 2)))
    
    def manhattan_distance(self, config1, config2):
        return float(np.sum(np.abs(config1 - config2)))

    def calculate_distance(self, config1, config2):
        if self.match_metric == 'euclidean':
            return self.euclidean_distance(config1, config2)
        elif self.match_metric == 'manhattan_distance':
            return self.manhattan_distance(config1, config2)
        else:
            raise ValueError(f"Invalid metric: {self.match_metric}. Must be one of {self.metrics}")
        

class config_matcher:
    def __init__(self, cpu_info, check_point_to_synthesis_name, match_metric='euclidean'):
        self.cpu_info = cpu_info
        self.synthesis_checkpoint_directory = f'../processors/checkpoints/{self.cpu_info.cpu_name}/Synthesis/'
        self.synthesis_checkpoint_record_history = f'../processors/checkpoints/{self.cpu_info.cpu_name}/Stored_Checkpoint_Record.json'
        self.match_metric = match_metric
        self.metric_calculator = match_metrics(self.match_metric)
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
    
    def prepare_checkpoint(self, checkpoint_config_index):
        try:
            # Use subprocess to execute the copy command with rename
            subprocess.run(
                ['cp', '-f', f'{self.synthesis_checkpoint_directory}{checkpoint_config_index}.dcp', f'{self.synthesis_checkpoint_directory}{self.check_point_to_synthesis_name}.dcp'],
                check=True  # Raises an error if the command fails
            )
            return True
        except subprocess.CalledProcessError as e:
            Exception(f"Error: {e}")


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
        best_config_name = None
        for key in stored_configs.keys():
            stored_config = stored_configs[key]
            stored_config = np.array([stored_config[param.name] for param in self.cpu_info.config_params.params])
            distance = self.metric_calculator.calculate_distance(stored_config, config_to_evaluate)
            if distance < min_distance:
                print(f'New best distance: {distance}')
                min_distance = distance
                best_config_name = key
        return best_config_name


if __name__ == '__main__':
    from interface import define_cpu_settings
    cpu_info, fpga_info = define_cpu_settings()
    matcher = config_matcher(cpu_info, "ChipTop")
    matcher.prepare_checkpoint("config_1")