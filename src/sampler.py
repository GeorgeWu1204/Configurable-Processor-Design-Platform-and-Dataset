from scipy.stats import qmc
import torch

class initial_sampler:
    def __init__(self, input_dim, constraint_set=None, data_set=None, gen_type=torch.float, gen_device=torch.device('cpu')):    
        # self.dim_ranges = constraint_set.get_self_bounds()
        self.input_dim = input_dim
        # The reason to use this sampler is that it could guarantee to only generate unique points.
        self.sampler = qmc.Sobol(d=self.input_dim, scramble=True)
        self.constraint_set = constraint_set
        self.data_set = data_set
        self.type = gen_type
        self.device = gen_device

    def generate_samples(self, num_samples):
        # Generate samples
        samples = torch.tensor(self.sampler.random(n=num_samples), device=self.device, dtype=self.type)
        return samples
    
    def generate_valid_initial_data(self, num_samples,output_dim, data_set, obj_normalized_factors):
        """This function is used to generate valid initial data that meet the input constraints and also the output constraints"""
        train_x = torch.empty((num_samples, self.input_dim), device=self.device, dtype=self.type)
        exact_objs = torch.empty((num_samples, output_dim), device=self.device, dtype=self.type)
        con_objs = torch.empty((num_samples, 1), device=self.device, dtype=self.type)
        normalised_objs = torch.empty((num_samples, output_dim), device=self.device, dtype=self.type)
        valid_sample_index = 0
        possible_initial_tensor = self.generate_samples(num_samples)

