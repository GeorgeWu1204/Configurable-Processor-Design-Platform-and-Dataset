import os.path as osp
from definitions import read_cpu_info_from_json
from constraints import target_fpga_info


def define_cpu_settings(mode):
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
    
    
    if mode == "Designing":
        for param in cpu_info.config_params.params:
            print(f"Parameter: {param.name} Default Value: {param.default_value} Range: {param.self_range}")
        choice = input("Load from existing configuration file? (y/n)")
        if choice == 'y':
            config_file = input("Enter the path to the configuration file: ")
            fpga_info = cpu_info.parse_proc_spec(config_file)
        else:
            #TODO
            print("Enter the configuration parameters: ")    
            while True:
                print("Enter the configuration parameters: ")
                config_name = input("Enter the name of the parameter: ")
                if not cpu_info.update_tunable_param(config_name):
                    print("The parameter does not exist in the database. Please try again.")
                    continue
                print(" Enter the range of the parameter: ")
                choice = input("Do you want to add more configuration parameters? (y/n): ")
                if choice == 'n':
                    break      
    elif mode == "Evaluation_Experiment":
        fpga_info = None              
    else:
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
                print("There are four performance metrics available for this benchmark")
                print("exe_time, throughput, mcycles, minstret")
                tmp_metrics = input("Type the metric you want to consider, split by ,")
                considered_metrics = tmp_metrics.split(", ")
                cpu_info.update_target_benchmark(output_name, considered_metrics)
            else:
                print("The benchmark does not exist in the database. Please try again.")
                continue
            choice = input("Do you want to add more benchmark? (y/n): ")
            if choice == 'n':
                break
    cpu_info.display_summary()
    return cpu_info, fpga_info


