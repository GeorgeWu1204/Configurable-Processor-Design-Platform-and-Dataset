import sys
from interface import define_cpu_settings
from dataset import Processor_Dataset

def main():
    # Define the settings of the CPU
    defined_cpu_info = define_cpu_settings()

    # Link the corresponding dataset
    processor_dataset = Processor_Dataset(defined_cpu_info)
    
    # Sampling Mode: Automatically exploring the design space
    if len(sys.argv) == 1 and sys.argv == "Sampling":
        pass
    # Querying Mode: Iteratively query the dataset, trying to find the PPA acc to the input.



if __name__ == "__main__":
    main()