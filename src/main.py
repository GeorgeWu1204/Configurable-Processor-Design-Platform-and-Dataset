import sys
from interface import define_cpu_settings
from dataset import Processor_Dataset, create_table_from_json


def main():
    # Define the settings of the CPU
    cpu_info, fpga_info = define_cpu_settings()
    # cpu_info.debug_print()
    # print()
    # create_table_from_json(cpu_info, '../dataset/PPA/BOOM_PPA.db')
    # Link the corresponding dataset
    processor_dataset = Processor_Dataset(cpu_info, fpga_info)

    # processor_dataset.debug_print()

    # Sampling Mode: Automatically exploring the design space
    if len(sys.argv) == 2 and sys.argv[1] == "Sampling":
        print("---------------Sampling Mode---------------")
        processor_dataset.design_space_exploration()


    # Querying Mode: Iteratively query the dataset, trying to find the PPA acc to the input.

if __name__ == "__main__":
    main()