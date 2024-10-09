import json
import os.path as osp

class conditional_constraints:
    def __init__(self, params_map):
        # Conditional Constraints in the following formats: [{A:[4,5], B: [5,6]}], representing if A in [4,5], then B should in [5,6]
        self.params_map = params_map
        self.conditional_constraints = []

    def update_conditional_constraints(self, extracted_constraint):
        conditional_constraints = {}
        for constraint_name in extracted_constraint:
            index = self.params_map[constraint_name]
            if index == None:
                raise ValueError("The name of the variables within the specified constraints does not meet requiremnet")
            conditional_constraints[index] = extracted_constraint[constraint_name]
        self.conditional_constraints.append(conditional_constraints)

    def check_conditional_constraints(self, new_design):
        if len(self.conditional_constraints) == 0:
            return True
        for conditional_constraint in self.conditional_constraints:
            for index in conditional_constraint.keys():
                if new_design[index] not in conditional_constraint[index]:
                    return False        
        return True


class target_fpga_info:
    def __init__(self, device_series_number):
        """This is the class storing the resource utilisation constraints specified by FPGA"""
        json_file = '../dataset/fpga/fpga_rc.json'
        if not osp.exists(json_file):
            raise FileNotFoundError(f"File {json_file} not found")
        with open(json_file, 'r') as file:
            data = json.load(file)
        for device in data:
            if device["Part"] == device_series_number:
                self.device = device
                self.series_number = device_series_number
                self.LUTs = device["LUT Elements"]
                self.FFs = device["FlipFlops"]
                self.BRAM = device["Block RAMs"]
                self.DSP = device["DSPs"]
        print(f"LUts: {self.LUTs}, FFs: {self.FFs}, BRAM: {self.BRAM}, DSP: {self.DSP}")
        self.rc_data_indexes_in_dataset = None
    
    def update_rc_data_indexes(self, indexes):
        self.rc_data_indexes_in_dataset = indexes

    def check_fpga_deployability(self, rc_data_in_dataset):
        print("rc_data_in_dataset", rc_data_in_dataset)
        if rc_data_in_dataset[0] < self.LUTs and rc_data_in_dataset[1] < self.FFs and rc_data_in_dataset[2] < self.BRAM and rc_data_in_dataset[3] < self.DSP:
            return True
        else:
            return False