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


class fpga_spec:
    def __init__(self, device_series_number):
        """This is the class storing the resource utilisation constraints specified by FPGA"""
        # Note the current dataset only focusing on the LUTs and FFs and the time analysis results.
        json_file = '../dataset/fpga/fpga_rc.json'
        if not osp.exists(json_file):
            raise FileNotFoundError(f"File {json_file} not found")
        with open(json_file, 'r') as file:
            data = json.load(file)
        for device in data:
            if device["Part"] == device_series_number:
                self.device = device
                self.series_number = device_series_number
                # self.IO_count = device["I\/O Pin Count"]
                # self.IOBs = device["Available IOBs"]
                self.LUTs = device["LUT Elements"]
                self.FFs = device["FlipFlops"]




def check_target_fpga_constraints():
    pass