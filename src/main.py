import sys
from interface import define_cpu_settings
from dataset import Processor_Dataset, create_table_from_json


def main():
    # Define the settings of the CPU
    cpu_info, fpga_info = define_cpu_settings()

    if "create_table" in sys.argv:
        create_table_from_json(cpu_info, f'../dataset/PPA/{cpu_info.cpu_name}_PPA.db')

    processor_dataset = Processor_Dataset(cpu_info, fpga_info)

    if "debug" in sys.argv:
        processor_dataset.debug_print()
        print()
        cpu_info.debug_print()


    if "Sampling" in sys.argv:
        # Sampling Mode: Automatically exploring the design space
        print("---------------Sampling Mode---------------")
        processor_dataset.design_space_exploration()
    elif "Querying" in sys.argv:
        # Querying Mode: Iteratively query the dataset, trying to find the PPA acc to the input.
        print("---------------Querying Mode---------------")
        processor_dataset.query_dataset()
    else:
        print("Invalid Mode")


if __name__ == "__main__":
    main()
    # import processor_tuner
    # cpu_info, fpga_info = define_cpu_settings()
    # test_tuner = processor_tuner.get_chip_tuner(cpu_info)
    # test_tuner.modify_custom_cpu(1)