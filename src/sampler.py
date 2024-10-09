import numpy as np
import pandas as pd
import os
class Sampler:
    def __init__(self, cpu_info):
        self.designspace_params = {}
        self.defualt_config = []
        for param in cpu_info.config_params.params:
            self.designspace_params[param.name] = param.self_range
            self.defualt_config.append(param.default_value)
        self.sample_file_name = f"../dataset/samples/{cpu_info.cpu_name}_samples.csv"
        self.sample_amount = 1000
        if not os.path.exists(self.sample_file_name):
            self.generate_samples()

    def save_samples(self, samples):
        samples = np.insert(samples, 0, self.defualt_config, axis=0)
        df = pd.DataFrame(samples, columns=self.designspace_params.keys())
        df['Evaluation Complete'] = 0
        df.to_csv(self.sample_file_name, index=False)

    def generate_samples(self):
        grids = {}
        for key, values in self.designspace_params.items():
            grids[key] = np.linspace(min(values), max(values), num=len(values))

        mesh = np.meshgrid(*grids.values())
        param_combinations = np.stack([m.flatten() for m in mesh], axis=-1)
        default_array = np.array(self.defualt_config)
        filtered_combinations = []
        for combo in param_combinations.reshape(-1, len(self.designspace_params)):
            if not np.array_equal(np.rint(combo).astype(int), default_array):
                filtered_combinations.append(combo)
        np.random.shuffle(filtered_combinations)
        selected_samples = filtered_combinations[:self.sample_amount - 1]
        rounded_samples = np.rint(selected_samples).astype(int)
        self.save_samples(rounded_samples)
        return rounded_samples
    
    def find_next_sample(self):
        df = pd.read_csv(self.sample_file_name)
        next_sample = df[df['Evaluation Complete'] == 0].iloc[0]
        return list(next_sample.values)[:-1]
    
    def mark_sample_complete(self, sample):
        df = pd.read_csv(self.sample_file_name)
        for index, row in df.iterrows():
            if np.array_equal(row.values[:-1], sample):
                df.at[index, 'Evaluation Complete'] = 1
                df.to_csv(self.sample_file_name, index=False)
                return True
        return False


if __name__ == "__main__":
    pass

