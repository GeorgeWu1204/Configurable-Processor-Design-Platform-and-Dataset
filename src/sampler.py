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

            # grids[key] = np.linspace(min(values), max(values), num=len(values))
            grids[key] = np.linspace(0, len(values) - 1, num=len(values))

        mesh = np.meshgrid(*grids.values())
        index_combination = np.stack([m.flatten() for m in mesh], axis=-1)
        default_array = np.array(self.defualt_config)
        default_array_index = np.zeros(len(self.designspace_params))
        for i, (key, values) in enumerate(self.designspace_params.items()):
            default_array_index[i] = values.index(default_array[i])
        print(default_array_index)
        filtered_index_combination = []
        for combo in index_combination.reshape(-1, len(self.designspace_params)):
            if not np.array_equal(np.rint(combo).astype(int), default_array_index):
                filtered_index_combination.append(combo)
        np.random.shuffle(filtered_index_combination)
        selected_samples_index_set = filtered_index_combination[:self.sample_amount - 1]
        selected_samples = []
        for index_set in selected_samples_index_set:
            sample = []
            for i, index in enumerate(index_set):
                sample.append(self.designspace_params[list(self.designspace_params.keys())[i]][int(index)])
            selected_samples.append(sample)
        self.save_samples(selected_samples)
    
    def find_next_sample(self):
        # This is to continue the evaluation of the samples, if the previous evaluation was terminated before completion due to various problems.
        df = pd.read_csv(self.sample_file_name)
        filtered_df = df[df['Evaluation Complete'] == 0]
        if not filtered_df.empty:
            next_sample = filtered_df.iloc[0]
            return list(next_sample.values)[:-1]
        else:
            return [] 
    
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

