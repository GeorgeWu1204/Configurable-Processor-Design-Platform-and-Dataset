import json
import random

def generate_random_designs(json_file, num_configs=3):
    """
    Generate random configurations based on the given JSON file.

    Args:
        json_file (str): Path to the JSON file.
        num_configs (int): Number of random configurations to generate.

    Returns:
        dict: Dictionary containing the generated configurations.
    """
    # Load the JSON file
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Extract configurable parameters
    configurable_params = data.get("Configurable_Params", {})

    # Generate random configurations
    configurations = {}
    for i in range(1, num_configs + 1):
        config = {}
        for param, details in configurable_params.items():
            self_range = details.get("self_range", [])
            param_type = details.get("type")

            if not self_range:
                continue

            # Randomly pick a value from the range
            if param_type == "int":
                if details.get("growth") == "linear":
                    value = random.randint(min(self_range), max(self_range))
                elif details.get("growth") == "discrete" or details.get("growth") == "exp2":
                    value = random.choice(self_range)
                else:
                    value = random.choice(self_range)
            elif param_type == "categorical":
                value = random.choice(self_range)
            else:
                value = random.choice(self_range)

            config[param] = value

        configurations[f"Config_{i}"] = config

    return configurations

# Example usage
if __name__ == "__main__":
    # input_file = "../../dataset/processor_configs/rocketchip_Config.json"  # Replace with your JSON file path
    # random_designs = generate_random_designs(input_file, num_configs=10)
    # stored_file = "random_rocketchip_designs.json"
    # with open(stored_file, 'w') as file:
    #     json.dump(random_designs, file, indent=4)
    input_file = "../../dataset/processor_configs/boom_Config.json"  # Replace with your JSON file path
    random_designs = generate_random_designs(input_file, num_configs=10)
    stored_file = "random_boom_designs.json"
    with open(stored_file, 'w') as file:
        json.dump(random_designs, file, indent=4)
