import re
import subprocess
from processor_config_matching import config_matcher
from GeneralChip import General_Chip_Tuner


class Rocket_Chip_Tuner(General_Chip_Tuner):
    """This is the tuner for scr1 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, cpu_info):
        super().__init__(cpu_info)
        # Log file for the generated reports
        self.generation_path = '../processors/chipyard/sims/verilator'
        self.cpu_level_config_file = '../processors/chipyard/generators/chipyard/src/main/scala/config/BoomConfigs.scala'
        self.core_level_configuration_file = '../processors/chipyard/generators/boom/src/main/scala/v3/common/config-mixins.scala'
        self.top_level_design_name = "ChipTop"
        self.processor_config_matcher = config_matcher(cpu_info, self.top_level_design_name)

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