import re
import subprocess
import os
import shutil

class EL2_VeeR_Tuner:
    """This is the tuner for EL2 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, tunable_params, shift_amount, generation_path, vivado_project_path):
        self.tunable_params = tunable_params        # A dictionary or list of parameters that can be tuned
        self.shift_amount = shift_amount            # The amount by which the parameters are shifted
        self.generation_path = generation_path      # Path to execute the generation command
        self.vivado_project_path = vivado_project_path
        self.tcl_path = '../../tools/EL2/run_EL2_synthesis.tcl'
        # Log file for the generated reports
        self.generated_report_num = 0
        self.generated_report_directory = '../processors/Syn_Report/'
        self.stored_report_directory = '../processors/Syn_Report/dynamic_set/'
        self.generated_filename = 'EL2_utilization_synth.rpt'
        self.generated_logfile = '../processors/Logs/'
        
    def tune_and_run_performance_simulation(self, new_value, benchmark):
        try:
            # Expand the environment variable
            rv_root = os.environ.get('RV_ROOT', '')  # Default to an empty string if RV_ROOT is not set
            if not rv_root:
                print("RV_ROOT environment variable is not set.")
                return False, None, None
            target = 'TEST=' + benchmark
            param_setting = 'CONF_PARAMS='
            for index, param in enumerate(self.tunable_params):
                if type(new_value[index]) == str:
                    # if the value is categorical
                    value = new_value[index]
                else:
                    value = str(round(new_value[index]) << self.shift_amount[index])
                param_setting+= '-set={param}={value} '.format(param=param, value=value)  
            param_setting += ''
            command = ['make', '-f', os.path.join(rv_root, 'tools/Makefile'), target, param_setting]
            # print(command)
            # Prepare the command with the expanded environment variable
            # Run the 'make' command in the directory where the Makefile is located
            with open(self.generated_logfile + 'Processor_Generation.log', 'w') as f:
                subprocess.run(command, check=True, stdout=f, stderr=f, cwd=self.generation_path)
            minstret, mcycle = self.extract_minstret_mcycle(self.generated_logfile + 'Processor_Generation.log')
            if mcycle is None:
                return False, None, None
            return True, minstret, mcycle
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred for the current benchmark {benchmark}")
            return False, None, None
    
    def run_synthesis(self):
        '''Run synthesis using the new parameters.'''
        command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", self.tcl_path]
        try:
            with open(self.generated_logfile + 'Synthesis.log', 'w') as f:
                subprocess.run(command, check=True, cwd=self.vivado_project_path, stdout=f, stderr=f)
        except subprocess.CalledProcessError as e:
            print(f"Error executing Vivado: {e}")
    
    def store_synthesis_report(self):
        '''Store the synthesis report in a file.'''
        name, extension = os.path.splitext(self.generated_filename)
        new_name = name + '_' + str(self.generated_report_num) + extension
        shutil.copy(self.generated_report_directory + self.generated_filename, self.stored_report_directory + new_name)
        self.generated_report_num += 1


    def extract_minstret_mcycle(self, log_file_path):
        """
        Extracts minstret and mcycle values from a log file.
        """
        # Regular expression to match the specific line and capture minstret and mcycle values
        pattern = r'Finished : minstret = (\d+), mcycle = (\d+)'

        # Initialize variables to store the extracted values
        minstret = None
        mcycle = None

        # Open the log file and read line by line
        try:
            with open(log_file_path, 'r') as file:
                for line in file:
                    # Search for the pattern in each line
                    match = re.search(pattern, line)
                    # If a match is found, extract the values
                    if match:
                        minstret = int(match.group(1))
                        mcycle = int(match.group(2))
                        # Break the loop after finding the first match
                        break
        except FileNotFoundError:
            print(f"Error: The file {log_file_path} was not found.")
            return None, None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None, None

        return minstret, mcycle
    


class Rocket_Chip_Tuner:
    """This is the tuner for scr1 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, tunable_params, shift_amount, generation_path, vivado_project_path):
        self.tunable_params = tunable_params        # A dictionary or list of parameters that can be tuned
        self.shift_amount = shift_amount            # The amount by which the parameters are shifted
        self.generation_path = generation_path      # Path to execute the generation command
        self.vivado_project_path = vivado_project_path
        self.tcl_path = '../../tools/RocketChip/run_RocketChip_synthesis.tcl'
        # Log file for the generated reports
        self.generated_report_num = 0
        self.generated_report_directory = '../processors/Syn_Report/'
        self.stored_report_directory = '../processors/Syn_Report/dynamic_set/'
        self.generated_filename = 'rocket_utilization_synth.rpt'
        self.generated_logfile = '../processors/Logs/'
        self.configuration_file = '../processors/rocket-chip/src/main/scala/subsystem/Configs.scala'

    def modify_config_files(self, input_vals):
            with open(self.configuration_file, 'r') as file:
                scala_code = file.read()
            
            # Regular expression to find the WithCustomisedCore class definition
            class_pattern = re.compile(r'class WithCustomisedCore\((.*?)\)\s*extends\s*Config\((.*?)=>\s*{(.*?)case RocketTilesKey\s*=>\s*{(.*?)}\s*}\)', re.DOTALL)
            match = class_pattern.search(scala_code)
            
            if match:
                params = match.group(1)
                body = match.group(4)
                for var_name, var_val in zip(self.tunable_params, input_vals):
                    class_name, sub_name = var_name.split('_')
                    print(class_name, sub_name)
                    if class_name == 'icache':
                        pattern = re.compile(r'icache\s*=\s*Some\(ICacheParams\((.*?)\)\)', re.DOTALL)
                        match = pattern.search(body)
                    elif class_name == 'dcache':
                        pattern = re.compile(r'dcache\s*=\s*Some\(DCacheParams\((.*?)\)\)', re.DOTALL)
                        match = pattern.search(body)
                    if match:
                        params = match.group(1)
                        sub_pattern = re.compile(rf'{sub_name}\s*=\s*\d+')
                        if sub_pattern.search(params):
                            new_params = sub_pattern.sub(f'{sub_name} = {var_val}', params)
                            new_body = body.replace(params, new_params)
                            scala_code = scala_code.replace(body, new_body)
                            body = new_body  # update the body for subsequent iterations
                        else:
                            print(f"{sub_name} not found in {class_name} parameters.")
                    else:
                        print(f"{class_name} class not found in the body.")
                with open(self.configuration_file, 'w') as file:
                    file.write(scala_code)
            else:
                print("WithCustomisedCore class definition not found.")

    def extract_mcycle_minstret(self):
        # Initialize variables to store mcycle and minstret
        mcycle = None
        minstret = None
        
        # Define the regex patterns to match the desired lines
        mcycle_pattern = re.compile(r'mcycle\s*=\s*(\d+)')
        minstret_pattern = re.compile(r'minstret\s*=\s*(\d+)')
        
        # Open the file and read its contents
        with open(self.generated_logfile + 'Processor_Generation.log', 'r') as file:
            lines = file.readlines()
        
        # Iterate over the lines to find the section and extract values
        for line in lines:
            if 'Microseconds for one run through Dhrystone:' in line:
                # Once we find the section, we start looking for mcycle and minstret
                for subsequent_line in lines[lines.index(line):]:
                    mcycle_match = mcycle_pattern.search(subsequent_line)
                    minstret_match = minstret_pattern.search(subsequent_line)
                    
                    if mcycle_match:
                        mcycle = int(mcycle_match.group(1))
                    
                    if minstret_match:
                        minstret = int(minstret_match.group(1))
                    
                    # Break the loop once both values are found
                    if mcycle is not None and minstret is not None:
                        break
        
        return mcycle, minstret

    def tune_and_run_performance_simulation(self, new_value, benchmark):
        try:
            # generate the design
            rounded_value = [round(val) for val in new_value]   
            self.modify_config_files(rounded_value)
            clean_command = ["make", "clean"]
            subprocess.run(clean_command, cwd = self.generation_path, check=True)
            run_benchmark_command = ["make", "-j12", "CONFIG=freechips.rocketchip.system.CustomisedConfig", f"output/{benchmark}.riscv.run"]
            with open(self.generated_logfile + 'Processor_Generation.log', 'w') as f:
                subprocess.run(run_benchmark_command, check=True, stdout=f, stderr=f, cwd=self.generation_path)
            minstret, mcycle = self.extract_mcycle_minstret()
            if mcycle is None:
                return False, None, None
            return True, minstret, mcycle
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred: {e}")
            return False, None, None
    
    def run_synthesis(self):
        '''Run synthesis using the new parameters.'''
        command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", self.tcl_path]
        try:
            with open(self.generated_logfile + 'Synthesis.log', 'w') as f:
                subprocess.run(command, check=True, cwd=self.vivado_project_path, stdout=f, stderr=f)
        except subprocess.CalledProcessError as e:
            print(f"Error executing Vivado: {e}")
    
    def store_synthesis_report(self):
        '''Store the synthesis report in a file.'''
        name, extension = os.path.splitext(self.generated_filename)
        new_name = name + '_' + str(self.generated_report_num) + extension
        shutil.copy(self.generated_report_directory + self.generated_filename, self.stored_report_directory + new_name)
        self.generated_report_num += 1


class BOOM_Chip_Tuner:
    """This is the tuner for scr1 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, cpu_info):
        self.generation_path = '../processors/chipyard/sims/verilator'
        self.vivado_project_path = '../processors/Vivado_Prj/BOOM_Prj/'
        self.tcl_path = '../../tools/BOOM/run_BOOM_synthesis.tcl'
        # Log file for the generated reports
        self.generated_report_num = 0
        self.generated_report_directory = '../processors/Logs/Syn_Report/'
        self.generated_utilisation_filename = 'BOOM_utilization_synth.rpt'
        self.generated_power_filename = 'BOOM_power_synth.rpt'
        self.generated_time_filename = 'BOOM_timing_synth.rpt'
        self.generated_logfile = '../processors/Logs/Generation_Log/Processor_Generation.log'
        self.cpu_level_config_file = '../processors/chipyard/generators/chipyard/src/main/scala/config/BoomConfigs.scala'
        self.core_level_configuration_file = '../processors/chipyard/generators/boom/src/main/scala/v3/common/config-mixins.scala'
        self.cpu_info = cpu_info
    
    def modify_custom_cpu(self, n):
        with open(self.cpu_level_config_file, 'r') as file:
            lines = file.readlines()
        pattern = re.compile(r'new boom\.v3\.common\.WithNCustomBooms\(\d+\)')
        for i, line in enumerate(lines):
            if 'class CustomisedBoomV3Config' in line:

                for j in range(i+1, len(lines)):
                    if pattern.search(lines[j]):
                        lines[j] = pattern.sub(f'new boom.v3.common.WithNCustomBooms({n})', lines[j])
                        break
                break
        with open(self.cpu_level_config_file, 'w') as file:
            file.writelines(lines)

    def modify_custom_core_internal_config(self, input_vals):
        # This is because the 0 index describing the number of cores.
        params_name = list(self.cpu_info.config_params.params_map.keys())[1:]
        with open(self.core_level_configuration_file, 'r') as file:
            lines = file.readlines()

        new_lines = []
        cache_context = None  # Track whether we're inside a dcache or icache block

        for line in lines:
            if 'DCacheParams' in line:
                cache_context = 'dcache'
            elif 'ICacheParams' in line:
                cache_context = 'icache'
            elif cache_context and ')' in line:  # Check for end of cache block
                cache_context = None
            
            modified_line = line
            if cache_context:
                for param, value in zip(params_name, input_vals):
                    if param.startswith(cache_context):
                        param_name = param.split('_')[1]
                        pattern = re.compile(rf'(\b{param_name}\s*=\s*)(\d+)')
                        modified_line = pattern.sub(r'\g<1>' + str(value), modified_line)  # Concatenation
            else:
                for param, value in zip(params_name, input_vals):
                    if not ('dcache' in param or 'icache' in param):
                        core_param_pattern = re.compile(rf'(\b{re.escape(param)}\s*=\s*)(\d+)')
                        modified_line = core_param_pattern.sub(r'\g<1>' + str(value), modified_line)  # Concatenation

            new_lines.append(modified_line)

        with open(self.core_level_configuration_file, 'w') as file:
            file.writelines(new_lines)

    def modify_config_files(self, input_vals):
        # CPU's overall configuration, Only modify the number of Cores
        self.modify_custom_cpu(input_vals[0])
        # Core's internal configuration
        self.modify_custom_core_internal_config(input_vals[1:])

    def extract_metrics_from_log(self):
        # Define the regular expressions to capture the required metrics
        time_pattern = r"Microseconds for one run through Dhrystone: (\d+)"
        throughput_pattern = r"Dhrystones per Second: +(\d+)"
        mcycles_pattern = r"mcycle = (\d+)"
        minstret_pattern = r"minstret = (\d+)"
        # Prepare to store the values
        metrics = {
            "exe_time": None,
            "throughput": None,
            "mcycles": None,
            "minstret": None
        }

        try:
            # Open the log file
            with open(self.generated_logfile, 'r') as file:
                # Read all lines from the file
                log_content = file.read()

                # Search for exe_time
                time_match = re.search(time_pattern, log_content)
                if time_match:
                    metrics["exe_time"] = int(time_match.group(1))

                # Search for throughput
                throughput_match = re.search(throughput_pattern, log_content)
                if throughput_match:
                    metrics["throughput"] = int(throughput_match.group(1))

                # Search for mcycles
                mcycles_match = re.search(mcycles_pattern, log_content)
                if mcycles_match:
                    metrics["mcycles"] = int(mcycles_match.group(1))

                # Search for minstret
                minstret_match = re.search(minstret_pattern, log_content)
                if minstret_match:
                    metrics["minstret"] = int(minstret_match.group(1))

        except FileNotFoundError:
            print(f"Error: The file {self.generated_logfile} does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")

        return metrics

    def tune_and_run_performance_simulation(self, new_value):
        try:
            # generate the design
            self.modify_config_files(new_value)
            clean_command = ["make", "clean"]
            subprocess.run(clean_command, cwd = self.generation_path, check=True)
            run_configure_command = ["make", "-j12", "CONFIG=CustomisedBoomV3Config"]
            subprocess.run(run_configure_command, cwd = self.generation_path, check=True)
            performance_results = {}
            for benchmark_to_examine in self.cpu_info.supported_output_objs.benchmark.metrics:
                run_benchmark_command = ["make", "run-binary", "CONFIG=CustomisedBoomV3Config", f"BINARY=../../toolchains/riscv-tools/riscv-tests/build/benchmarks/{benchmark_to_examine}.riscv"]
                with open(self.generated_logfile, 'w') as f:
                    subprocess.run(run_benchmark_command, check=True, stdout=f, stderr=f, cwd=self.generation_path)
                performance_results[benchmark_to_examine] = self.extract_metrics_from_log()

            if len(performance_results) == 0:
                return False, None
            return True, performance_results
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred: {e}")
            return False, None
    
    def run_synthesis(self):
        '''Run synthesis using the new parameters.'''
        command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", self.tcl_path]
        try:
            with open(self.generated_logfile, 'w') as f:
                subprocess.run(command, check=True, cwd=self.vivado_project_path, stdout=f, stderr=f)
        except subprocess.CalledProcessError as e:
            print(f"Error executing Vivado: {e}")
    

    def parse_vivado_resource_utilisation_report(self):
        # Define the dictionary to hold the results
        resource_info = {
            "LUTs": 0,
            "FFs": 0,
            "BRAM": 0,
            "DSP": 0
        }
        
        # Define the regular expressions for each resource type
        patterns = {
            "LUTs": re.compile(r"\|\s*CLB LUTs*\s*\|\s*(\d+)\s*\|"),
            "FFs": re.compile(r"\|\s*CLB Registers\s*\|\s*(\d+)\s*\|"),
            "BRAM": re.compile(r"\|\s*Block RAM Tile\s*\|\s*(\d+)\s*\|"),
            "DSP": re.compile(r"\|\s*DSPs\s*\|\s*(\d+)\s*\|")
        }
        
        # Open the report file
        with open(self.generated_report_directory + self.generated_utilisation_filename, 'r') as file:
            # Read through each line of the file
            for line in file:
                # Check each pattern to see if it matches the line
                for key, pattern in patterns.items():
                    match = pattern.search(line)
                    if match:
                        # If there's a match, store the number in the corresponding dictionary key
                        resource_info[key] = int(match.group(1))
        
        return resource_info
    
    def parse_vivado_power_report(self):
        power_info = {
            "Dynamic": 0.0,
            "Static": 0.0
        }
        pattern = {
            "Dynamic": re.compile(r"\|\s*Dynamic \(W\)\s*\|\s*([\d.]+)\s*\|"),
            "Static": re.compile(r"\|\s*Device Static \(W\)\s*\|\s*([\d.]+)\s*\|")
        }
        with open(self.generated_report_directory + self.generated_power_filename, 'r') as file:
            for line in file:
                for key, pat in pattern.items():
                    match = pat.search(line)
                    if match:
                        power_info[key] = float(match.group(1))
        return power_info
    
    def extract_wns(self):
        wns = None
        wns_pattern = re.compile(r"\s+(-?\d+\.\d+)\s+")
        with open(self.generated_report_directory + self.generated_time_filename, 'r') as file:
            in_timing_summary = False     
            for line in file:
                if 'WNS(ns)' in line and 'TNS(ns)' in line:
                    in_timing_summary = True
                    continue
                if in_timing_summary and '-------' not in line:
                    wns_match = wns_pattern.search(line)
                    if wns_match:
                        wns = float(wns_match.group(1))
                        break
        return wns
    
    def parse_vivado_timing_report(self):
        timing_info = {
            "Period": 20, # Default value acc to time_constraints.xdc
            "WNS" : 0,
            "Setup_Worst_Slack": 0,
            "Hold_Worst_Slack": 0,
            "PW_Worst_Slack": 0
        }

        # Define regex patterns to match the lines with worst slack values
        setup_pattern = r"Setup\s*:\s*\d+\s*Failing Endpoints,\s*Worst Slack\s*([-+]?\d*\.?\d+ns)"
        hold_pattern = r"Hold\s*:\s*\d+\s*Failing Endpoints,\s*Worst Slack\s*([-+]?\d*\.?\d+ns)"
        pw_pattern = r"PW\s*:\s*\d+\s*Failing Endpoints,\s*Worst Slack\s*([-+]?\d*\.?\d+ns)"
        
        setup_worst_slack = None
        hold_worst_slack = None
        pw_worst_slack = None
        
        # Read the file and search for the patterns
        with open(self.generated_report_directory + self.generated_time_filename, 'r') as file:
            for line in file:
                if not setup_worst_slack:
                    setup_match = re.search(setup_pattern, line)
                    if setup_match:
                        setup_worst_slack = setup_match.group(1)
                        
                if not hold_worst_slack:
                    hold_match = re.search(hold_pattern, line)
                    if hold_match:
                        hold_worst_slack = hold_match.group(1)
                if not pw_worst_slack:
                    pw_match = re.search(pw_pattern, line)
                    if pw_match:
                        pw_worst_slack = pw_match.group(1)
                # If both values are found, no need to continue reading
                if setup_worst_slack and hold_worst_slack and pw_worst_slack:
                    break
        timing_info["Setup_Worst_Slack"] = float(setup_worst_slack.split('ns')[0])
        timing_info["Hold_Worst_Slack"] = float(hold_worst_slack.split('ns')[0])
        timing_info["PW_Worst_Slack"] = float(pw_worst_slack.split('ns')[0])
        timing_info["WNS"] = self.extract_wns()
        return timing_info
    



if __name__ == '__main__':

    # print(extract_wns('../processors/Logs/Syn_Report/BOOM_timing_synth.rpt'))
    pass