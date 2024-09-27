import numpy as np

def generate_samples(sample_num, data_dimension, ranges):
    if len(ranges) != data_dimension:
        raise ValueError("Length of ranges must match the data dimension.")
    # Calculate number of points per dimension by rounding to the nearest integer
    points_per_dimension = int(sample_num ** (1 / data_dimension))
    # Create grid for each dimension based on its range
    grids = [np.linspace(r[0], r[1], points_per_dimension) for r in ranges]
    # Create meshgrid to get all combinations of the grid points
    mesh = np.meshgrid(*grids)
    # Stack the meshgrid into a sample matrix
    sample_matrix = np.stack(mesh, axis=-1).reshape(-1, data_dimension)
    # If the number of samples is larger than required, truncate the samples
    if sample_matrix.shape[0] > sample_num:
        sample_matrix = sample_matrix[:sample_num]
    return sample_matrix

# Example usage
sample_num = 100
data_dimension = 2
ranges = [(0, 10), (5, 15)]

samples = generate_samples(sample_num, data_dimension, ranges)
print(samples)
