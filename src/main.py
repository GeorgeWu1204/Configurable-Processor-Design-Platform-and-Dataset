import sys
from interface import define_cpu_settings
from dataset import Processor_Dataset, create_table_from_json


def main():
    # Define the settings of the CPU
    cpu_info, fpga_info = define_cpu_settings()
    # cpu_info.debug_print()
    # quit()
    print()
    create_table_from_json(cpu_info, '../dataset/PPA/BOOM_PPA.db')
    quit()
    # Link the corresponding dataset
    processor_dataset = Processor_Dataset(cpu_info, fpga_info)
    # processor_dataset.debug_print()
    processor_dataset.tuner.tune_and_run_performance_simulation([1, 4, 1, 32, 64, 4, 8, 64, 4])
    quit()
    # Sampling Mode: Automatically exploring the design space
    if len(sys.argv) == 1 and sys.argv == "Sampling":
        pass
    # Querying Mode: Iteratively query the dataset, trying to find the PPA acc to the input.
    # processor_dataset.insert_single_data([8, 8, 8, 8, 4, 4, 0, 0, 0, 0, 0, 0, 0 , 0, 0])
    print(processor_dataset.fetch_single_data_acc_to_def([10]))

if __name__ == "__main__":
    main()