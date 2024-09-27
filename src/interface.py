import os.path as osp
from utils import read_cpu_info_from_json
from constraints import target_fpga_info

def define_cpu_settings():
    # CPU Info
    while True:
        name = input("Enter the name of the CPU or type 'exit' to quit: ")
        if name.lower() == 'exit':
            exit("Exiting the program.")
        if osp.exists(f'../dataset/processor_configs/{name.lower()}_Config.json'):
            break
        else:
            print("The CPU does not exist in the database. Please try again.")
    cpu_info = read_cpu_info_from_json(f'../dataset/processor_configs/{name.lower()}_Config.json')
    
    # FPGA Info
    while True:
        fpga_device = input(" If consider the deployability on target FPGA, enter target FPGA series number \n Otherwise, type SIM to ignore this ")
        if fpga_device.lower() == 'sim':
            fpga_info = None
            break
        fpga_info = target_fpga_info(fpga_device)
        if fpga_info is not None:
            break

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
    print(f"The existing supported RISC-V benchmarks for {cpu_info.cpu_name} are:")
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
    return cpu_info, fpga_info
