import sys
from interface import define_cpu_settings
from dataset import Processor_Dataset, create_table_from_json


def main():
    # Define the settings of the CPU
    defined_cpu_info = define_cpu_settings()
    defined_cpu_info.debug_print()

    # create_table_from_json(defined_cpu_info, '../dataset/PPA/RocketChip_PPA.db')

    # Link the corresponding dataset
    processor_dataset = Processor_Dataset(defined_cpu_info)
    processor_dataset.debug_print()

    # Sampling Mode: Automatically exploring the design space
    if len(sys.argv) == 1 and sys.argv == "Sampling":
        pass
    # Querying Mode: Iteratively query the dataset, trying to find the PPA acc to the input.
    # processor_dataset.insert_single_data([8, 8, 8, 8, 4, 4, 0, 0, 0, 0, 0, 0, 0 , 0, 0])
    print(processor_dataset.fetch_single_data_acc_to_def([8]))

if __name__ == "__main__":
    main()