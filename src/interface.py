import os.path as osp
from utils import read_cpu_info_from_json, read_fpga_info_from_json

def define_cpu_settings():
    # CPU Info
    while True:
        name = input("Enter the name of the CPU: ")
        if osp.exists(f'../dataset/constraints/{name}_Config.json'):
            break
        else:
            print("The CPU does not exist in the database. Please try again.")

    cpu_info = read_cpu_info_from_json(f'../dataset/constraints/{name}_Config.json')
    while True:
        fpga_device = input("Enter the target FPGA: ")
        targetfpga = read_fpga_info_from_json(fpga_device)
        if targetfpga is not None:
            break
    cpu_info.add_target_fpga(targetfpga)
    # Tunable Params
    while True:
        print("Enter the configuration parameters: ")
        config_name = input("Enter the name of the parameter: ")
        if not cpu_info.update_tunable_param(config_name):
            print("The parameter does not exist in the database. Please try again.")
            continue
        choice = input("Do you want to add more configuration parameters? (y/n): ")
        if choice == 'n':
            break
    # Output Params
    print(f"The existing benchmarks for {cpu_info.cpu_name} are:")
    supported_benchmarks = cpu_info.supported_output_objs.benchmark.metrics
    print(supported_benchmarks)
    while True:
        output_name = input("Enter the name of the RISC-V benchmark: ")
        if output_name in supported_benchmarks:
            cpu_info.update_target_objs(output_name)
        else:
            print("The benchmark does not exist in the database. Please try again.")
            continue
        choice = input("Do you want to add more output parameters? (y/n): ")
        if choice == 'n':
            break
    return cpu_info
