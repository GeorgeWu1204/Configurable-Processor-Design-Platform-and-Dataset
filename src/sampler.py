# encoding: utf-8
import numpy as np
import pandas as pd
import os
from OA_Sample.OAT import *
import json
import random


def adjust_design_space(design_space, max_levels_per_variable):

    adjusted_space = []
    for (name, tunable_range), max_levels in zip(design_space, max_levels_per_variable):
        if max_levels == len(tunable_range):
            adjusted_space.append((name, list(tunable_range)))
        else:
            if max_levels < len(tunable_range):
                evenly_selected_levels = np.linspace(0, len(tunable_range) - 1, max_levels, dtype=int)
                adjusted_space.append((name, [tunable_range[int(level)] for level in evenly_selected_levels]))
            else:
                adjusted_space.append((name, list(tunable_range) + [random.choice(tunable_range) for _ in range(max_levels - len(tunable_range))]))

    return adjusted_space

def round_to_nearest_power_of_two(arr):
    def nearest_power_of_two(x):
        if x == 0:
            return 0  # Edge case: zero stays zero
        lower = 2 ** (np.floor(np.log2(x)))
        upper = 2 ** (np.ceil(np.log2(x)))
        return lower if abs(x - lower) <= abs(x - upper) else upper

    vectorized_func = np.vectorize(nearest_power_of_two)
    return vectorized_func(arr).astype(int)



class Sampler:
    def __init__(self, cpu_info):
        self.design_space_params = {}
        self.defualt_config = []
        for param in cpu_info.config_params.params:
            self.design_space_params[param.name] = param.self_range
            self.defualt_config.append(param.default_value)
        
        self.params_order = {}
        for i, param in enumerate(cpu_info.config_params.params):
            self.params_order[param.name] = param.index
        self.sample_file_name = f"../dataset/samples/{cpu_info.cpu_name}_samples.csv"
        self.sample_oat_file_name = f"../dataset/samples/{cpu_info.cpu_name}_oat_samples.csv"
        # The number of samples to be generated for the design space exploration for the linear distribution mode.
        self.sample_amount = 1000
        # For OAT, utilising the minimal OAT construction methods.
        self.max_levels_per_variable = [len(tunable_range) for tunable_range in self.design_space_params.values()]
        self.max_levels_per_variable = round_to_nearest_power_of_two(self.max_levels_per_variable)
        self.max_levels_per_variable = [4, 4, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2]

        if not os.path.exists(self.sample_file_name):
            self.generate_samples()
        
        if not os.path.exists(self.sample_oat_file_name):
            self.generate_samples_acc_to_OAT()

    def save_samples(self, samples):
        samples = np.insert(samples, 0, self.defualt_config, axis=0)
        df = pd.DataFrame(samples, columns=self.design_space_params.keys())
        df['Evaluation Complete'] = 0
        df.to_csv(self.sample_file_name, index=False)

    def generate_samples(self):
        # This is the generalised way to generate samples for the design space exploration with the given sample amount.
        grids = {}
        for key, values in self.design_space_params.items():
            grids[key] = np.linspace(0, len(values) - 1, num=len(values))

        mesh = np.meshgrid(*grids.values())
        index_combination = np.stack([m.flatten() for m in mesh], axis=-1)
        default_array = np.array(self.defualt_config)
        default_array_index = np.zeros(len(self.design_space_params))
        for i, (key, values) in enumerate(self.design_space_params.items()):
            default_array_index[i] = values.index(default_array[i])
        print(default_array_index)
        filtered_index_combination = []
        for combo in index_combination.reshape(-1, len(self.design_space_params)):
            if not np.array_equal(np.rint(combo).astype(int), default_array_index):
                filtered_index_combination.append(combo)
        np.random.shuffle(filtered_index_combination)
        selected_samples_index_set = filtered_index_combination[:self.sample_amount - 1]
        selected_samples = []
        for index_set in selected_samples_index_set:
            sample = []
            for i, index in enumerate(index_set):
                sample.append(self.design_space_params[list(self.design_space_params.keys())[i]][int(index)])
            selected_samples.append(sample)
        self.save_samples(selected_samples)
    
    def generate_samples_acc_to_OAT(self):
        # This is the generalised way to generate samples for the design space exploration with the given sample amount.
        oat = OAT()
        case = []
        for key, values in self.design_space_params.items():
            case.append((key, values))  # Fix: Correct tuple construction.
        print("Case:", case)
        # Assuming the first tuple contains valid key-value pairs for OrderedDict.
        adjusted_case = adjust_design_space(case, self.max_levels_per_variable)
        for i, (name, values) in enumerate(adjusted_case):
            print(f"{name}: {len(values)}")

        generated_samples = OrderedDict(adjusted_case) 
        samples = oat.genSets(generated_samples, 0, 0)

        selected_samples = [
        [item[key] for key in sorted(item.keys(), key=lambda k: self.params_order[k])] 
        for item in samples
        ]

        results = []
        params_name  = list(self.design_space_params.keys())
        for sample in selected_samples:
            modified_sample = []
            for i, param in enumerate(sample):
                if param == None:
                    modified_sample.append(random.choice(self.design_space_params[params_name[i]]))
                else:
                    modified_sample.append(param)
            results.append(modified_sample)


        print("results:", results)
        # print("Default Config:", self.defualt_config)

        generated_samples = np.insert(results, 0, self.defualt_config, axis=0)
        
        df = pd.DataFrame(generated_samples, columns=self.design_space_params.keys())
        df['Evaluation Complete'] = 0
        df.to_csv(self.sample_oat_file_name, index=False)

    def find_next_sample(self, sampling_mode = 'default'):
        # This is to continue the evaluation of the samples, if the previous evaluation was terminated before completion due to various problems.
        if sampling_mode == 'default':
            df = pd.read_csv(self.sample_file_name)
        elif sampling_mode == 'oat':
            df = pd.read_csv(self.sample_oat_file_name)
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
    oat = OAT()

    # test = [('Core_Num', [1, 2, 3, 4]), ('Branch_Predictor', ['WithTAGELBPD', 'WithBoom2BPD', 'WithAlpha21264BPD', 'WithSWBPD']), ('enablePrefetching', ['true', 'false']), ('fetchWidth', [1, 2, 3, 4]), ('decodeWidth', [1, 2, 4, 8, 16])]
    test = OrderedDict([('A', ['A1', 'A2', 'A3', 'A4']),
                         ('B', ['B1', 'B2']),
                         ('C', ['C1', 'C2']),
                         ('D', ['D1', 'D2']),
                         ('E', ['E1', 'E2'])])

    # case = OrderedDict(test)
    case1 = OrderedDict(test)
    selected_case = oat.genSets(case1, 1, 0)
    list_of_lists = [list(item.values()) for item in selected_case]
    print("Selected Case:", list_of_lists)
    # print("Selected Case:", [ param.values() for param in json.dumps(selected_case)[0]])
    # result  = [i[1] for i in selected_case]
