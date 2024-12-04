import os
from interface import define_cpu_settings
from dataset import Processor_Dataset, create_table_from_json
from design_methods.design_framework import Design_Framework
from processor_tuner.processor_config_matching import analyse_config_weights_for_synthesis

import argparse

def main(mode, debug=False, create_table=False):
    # Define the settings of the CPU
    cpu_info, fpga_info = define_cpu_settings(mode)

    if create_table == True or not os.path.exists(f'../dataset/PPA/{cpu_info.cpu_name}_PPA.db'):
        create_table_from_json(cpu_info, f'../dataset/PPA/{cpu_info.cpu_name}_PPA.db')

    processor_dataset = Processor_Dataset(cpu_info, fpga_info)

    if debug == True:
        processor_dataset.debug_print()
        print()
        cpu_info.debug_print()

    if mode == "Sampling":
        # Sampling Mode: Automatically exploring the design space
        print("---------------Sampling Mode---------------")
        processor_dataset.design_space_exploration()
    elif mode == "Querying":
        # Querying Mode: Iteratively query the dataset, trying to find the PPA acc to the input.
        print("---------------Querying Mode---------------")
        processor_dataset.query_dataset()
    
    elif mode == "Designing":
        # Designing Mode: Designing the processor based on the dataset.
        print("---------------Designing Mode---------------")
        df = Design_Framework(cpu_info, processor_dataset)
        df.run_optimisation()
    elif mode == "Analyse_Weights":
        # Analyse Weights Mode: Analyse the weights of the configurations for synthesis
        print("---------------Analyse Weights Mode---------------")
        analyse_config_weights_for_synthesis(processor_dataset)
    else:
        print("Invalid Mode")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument('--mode', type=str, help='An operation mode')
    parser.add_argument('--debug', type=bool, help='Whether to print debug information')
    parser.add_argument('--create_table', type=bool, help='Whether to create the table from the json file')
    args = parser.parse_args()
    main(args.mode, args.debug, args.create_table)