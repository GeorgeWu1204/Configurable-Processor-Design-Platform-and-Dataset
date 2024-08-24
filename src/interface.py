import json
from definition import object_cpu_info, config_param

def input_cpu_info():
    name = input("Enter the name of the CPU: ")
    target_fpga = input("Enter the target FPGA: ")
    config_params = []
    output_params = []
    while True:
        print("Enter the configuration parameters: ")
        config_name = input("Enter the name of the parameter: ")
        config_type = input("Enter the type of the parameter: ")
        config_value = input("Enter the value of the parameter: ")
        config_params.append(config_param(config_name, config_type, config_value))
        choice = input("Do you want to add more configuration parameters? (y/n): ")
        if choice == 'n':
            break
    while True:
        print("Enter the output parameters: ")
        output_name = input("Enter the name of the parameter: ")
        output_type = input("Enter the type of the parameter: ")
        output_params.append(config_param(output_name, output_type, None))
        choice = input("Do you want to add more output parameters? (y/n): ")
        if choice == 'n':
            break
    return object_cpu_info(name, config_params, output_params, target_fpga)
