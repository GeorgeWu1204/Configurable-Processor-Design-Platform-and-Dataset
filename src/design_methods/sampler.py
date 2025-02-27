from scipy.stats import qmc
import torch
import time

class initial_sampler:
    def __init__(self, input_dim, output_dim, constraint_set=None, processor_analyser=None, gen_type=torch.float, gen_device=torch.device('cpu')):
        self.input_dim = input_dim
        self.constraint_set = constraint_set
        self.processor_analyser = processor_analyser
        self.type = gen_type
        self.device = gen_device
        self.sample_counter = 0  # Introduce a sample counter to add variability to the seed
        self.output_dim = output_dim

    def generate_samples(self, num_samples):
        # Dynamic seeding mechanism: combine time and sample counter
        seed = int(time.time()) + self.sample_counter
        self.sample_counter += 1  # Increment counter to ensure different seeds in successive calls
        
        self.sampler = qmc.Sobol(d=self.input_dim, scramble=True, seed=seed)
        
        # Generate samples
        samples = torch.tensor(self.sampler.random(n=num_samples), device=self.device, dtype=self.type)
        return samples
    
    def generate_valid_initial_data(self, num_samples):
        """This function is used to generate valid initial data that meet the input constraints and also the output constraints"""
        train_x = torch.empty((num_samples, self.input_dim), device=self.device, dtype=self.type)
        exact_objs = torch.empty((num_samples, self.output_dim), device=self.device, dtype=self.type)
        con_objs = torch.empty((num_samples, 1), device=self.device, dtype=self.type)
        normalised_objs = torch.empty((num_samples, self.output_dim), device=self.device, dtype=self.type)
        valid_sample_index = 0
        print("Start Initial Sampling")
        while (valid_sample_index) <= int(num_samples/2):
            possible_initial_tensor = self.generate_samples(num_samples)
            for i in range(num_samples):
                if self.constraint_set.check_single_point_meet_constraint(possible_initial_tensor[i,:]) == False:
                    continue
                # check internal constraints
                valid_sample, possible_obj = self.processor_analyser.find_evaluation_results(possible_initial_tensor[i:i+1,:])
                # if the generated desgin does not meet the internal constraints that are not disclosed in the spec.
                if valid_sample == False:
                    continue
                normalised_obj = self.processor_analyser.normalise_output_data_tensor(possible_obj)
                con_obj = self.processor_analyser.check_obj_constraints(normalised_obj)
                if con_obj.item() <= 0.0:
                    train_x[valid_sample_index] = possible_initial_tensor[i,:]
                    exact_objs[valid_sample_index] = possible_obj
                    con_objs[valid_sample_index] = con_obj
                    normalised_objs[valid_sample_index] = normalised_obj
                    valid_sample_index += 1
                    if valid_sample_index >= num_samples:
                        return train_x, exact_objs, con_objs, normalised_objs
        return train_x[:valid_sample_index, : ], exact_objs[:valid_sample_index, :], con_objs[:valid_sample_index, :], normalised_objs[:valid_sample_index, :]

# class single_sampler(initial_sampler):
#     def __init__(self, input_dim, output_dim, constraint_set=None, processor_analyser=None, gen_type=torch.float, gen_device=torch.device('cpu')):
#         super(single_sampler, self).__init__(input_dim, output_dim, constraint_set, processor_analyser, gen_type, gen_device)
#         self.output_dim = 1

#     def generate_valid_initial_data(self, num_samples, processor_analyser):
#         """This function is used to generate valid initial data that meet the input constraints and also the output constraints"""
#         train_x = torch.empty((num_samples, self.input_dim), device=self.device, dtype=self.type)
#         exact_objs = torch.empty((num_samples, self.output_dim), device=self.device, dtype=self.type)
#         con_objs = torch.empty((num_samples, 1), device=self.device, dtype=self.type)
#         normalised_objs = torch.empty((num_samples, self.output_dim), device=self.device, dtype=self.type)
#         valid_sample_index = 0
#         while (valid_sample_index) <= int(num_samples/2):
#             possible_initial_tensor = self.generate_samples(num_samples)
#             for i in range(num_samples):
#                 if self.constraint_set.check_single_point_meet_constraint(possible_initial_tensor[i,:]) == False:
#                     continue
#                 # check internal constraints
#                 valid_sample, possible_obj = processor_analyser.find_evaluation_results(possible_initial_tensor[i:i+1,:])
#                 # if the generated desgin does not meet the internal constraints that are not disclosed in the spec.
#                 if valid_sample == False:
#                     continue
#                 normalised_obj = processor_analyser.normalise_output_data_tensor(possible_obj)
#                 con_obj = processor_analyser.check_obj_constraints(normalised_obj)
#                 if con_obj.item() <= 0.0:
#                     train_x[valid_sample_index] = possible_initial_tensor[i,:]
#                     exact_objs[valid_sample_index] = possible_obj
#                     con_objs[valid_sample_index] = con_obj
#                     normalised_objs[valid_sample_index] = normalised_obj
#                     valid_sample_index += 1
#                     if valid_sample_index >= num_samples:
#                         return train_x, exact_objs, con_objs, normalised_objs


#         return train_x[:valid_sample_index, : ], exact_objs[:valid_sample_index, :], con_objs[:valid_sample_index, :], normalised_objs[:valid_sample_index, :]
