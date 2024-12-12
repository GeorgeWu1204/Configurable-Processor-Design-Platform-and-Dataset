import re
import subprocess
from .processor_config_matching import config_matcher
from .GeneralChip import General_Chip_Tuner


class Rocket_Chip_Tuner(General_Chip_Tuner):
    """This is the tuner for scr1 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, cpu_info):
        super().__init__(cpu_info)
        # Log file for the generated reports
        self.generation_path = '../processors/chipyard/sims/verilator'
        self.cpu_level_config_file = '../processors/chipyard/generators/chipyard/src/main/scala/config/RocketConfigs.scala'
        self.core_level_configuration_file = '../processors/chipyard/generators/rocket-chip/src/main/scala/rocket/Configs.scala'
        self.top_level_design_name = "DigitalTop"
        self.processor_config_matcher = config_matcher(cpu_info, self.top_level_design_name)


    def modify_cpu_config(self, num_cores, customised_configs):
        with open(self.cpu_level_config_file, 'r') as file:
            lines = file.readlines()
        pattern = re.compile(r'new freechips\.rocketchip\.rocket\.WithCustomisedCore\(\d+\)')
        assert len(customised_configs) == 3 # FPU, MulDiv, Btb
        for i, line in enumerate(lines):
            if 'class CustomisedRocketConfig' in line:
                for j in range(i+1, len(lines)):
                    if pattern.search(lines[j]):
                        lines[j] = pattern.sub(f'new freechips.rocketchip.rocket.WithCustomisedCore({num_cores})', lines[j])
                        # Remove Previous Customised Configurations
                        for m in range(j+1, len(lines)):
                            # Ugly way to remove the previous customised configurations, can be improved
                            pattern_to_delete = r'new freechips\.rocketchip\.rocket\.\w+\s*\+\+'
                            if re.search(pattern_to_delete, lines[j + 1]):
                                print("Deleting: ", lines[j + 1])
                                lines.pop(j + 1)
                            else:
                                break
                        # Add New Customised Configurations
                        index = 0
                        if customised_configs[0] != "DefaultFPU":
                            index += 1
                            lines.insert(j + index, f'  new freechips.rocketchip.rocket.{customised_configs[0]} ++\n')
                        if customised_configs[1] != "DefaultMulDiv":
                            index += 1
                            lines.insert(j + index, f'  new freechips.rocketchip.rocket.{customised_configs[1]} ++\n')
                        if customised_configs[2] != "WithDefaultBtb":
                            index += 1
                            lines.insert(j + index, f'  new freechips.rocketchip.rocket.{customised_configs[2]} ++\n')
                        break
                break
        with open(self.cpu_level_config_file, 'w') as file:
            file.writelines(lines)

    def modify_peripheral_and_core_config(self, input_vals):
            params_name = list(self.cpu_info.config_params.params_map.keys())[-len(input_vals):]
            with open(self.core_level_configuration_file, 'r') as file:
                scala_code = file.read()
            
            # Regular expression to find the WithCustomisedCore class definition
            class_pattern = re.compile(
                    r'class\s+WithCustomisedCore\(\s*n:\s*Int,\s*crossing:\s*RocketCrossingParams\s*=\s*RocketCrossingParams\(\s*\),\s*\)\s*extends\s*Config\(\(site,\s*here,\s*up\)\s*=>\s*{\s*(.*?)\s*}\)',
                    re.DOTALL)
            core_pattern = re.compile(r"(core = RocketCoreParams\()(useVM = )(true|false)(, useAtomics = )(true|false)(, useCompressed = )(true|false)(\))")

            match = class_pattern.search(scala_code)

            if match:
                config_body = match.group(1)  # Corrected to match the single capture group
                for var_name, var_val in zip(params_name, input_vals):
                    print(var_name, var_val)
                    if '_' not in var_name:
                        class_name = 'core'
                    else:
                        class_name, sub_name = var_name.split('_')
                    modify_core = False
                    cache_match = None
                    # Cache Configuration
                    if class_name == 'icache':
                        pattern = re.compile(rf'icache\s*=\s*Some\(ICacheParams\((.*?)\)\)', re.DOTALL)
                        cache_match = pattern.search(config_body)
                    elif class_name == 'dcache':
                        pattern = re.compile(rf'dcache\s*=\s*Some\(DCacheParams\((.*?)\)\)', re.DOTALL)
                        cache_match = pattern.search(config_body)
                    else:
                        modify_core = True
                    if cache_match:
                        params = cache_match.group(1)
                        sub_pattern = re.compile(rf'{sub_name}\s*=\s*\d+')
                        if sub_pattern.search(params):
                            new_params = sub_pattern.sub(f'{sub_name} = {var_val}', params)
                            new_cache_body = cache_match.group(0).replace(params, new_params)
                            config_body = config_body.replace(cache_match.group(0), new_cache_body)
                        else:
                            print(f"{sub_name} not found in {class_name} parameters.")
                    # Extension Enable
                    if modify_core:
                        core_match = core_pattern.search(config_body)
                        if core_match:
                            core_params = core_match.group(0)
                            sub_pattern = re.compile(rf'{var_name} = (true|false)')
                            if sub_pattern.search(core_params):
                                new_params = sub_pattern.sub(f'{var_name} = {var_val}', core_params)
                                config_body = config_body.replace(core_params, new_params)
                            else:
                                print(f"{var_name} not found in core parameters.")


                # Rewrite the modified block back into the scala_code
                scala_code = class_pattern.sub(f'class WithCustomisedCore(\n  n: Int,\n  crossing: RocketCrossingParams = RocketCrossingParams(),\n) extends Config((site, here, up) => {{\n{config_body}}})', scala_code)

                with open(self.core_level_configuration_file, 'w') as file:
                    file.write(scala_code)
            else:
                print("WithCustomisedCore class definition not found.")


    def modify_config_files(self, input_vals):
        # CPU's overall configuration, Only modify the number of Cores
        self.modify_cpu_config(input_vals[0], input_vals[1:4])
        # Core's internal configuration
        self.modify_peripheral_and_core_config(input_vals[4:])

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

    def tune_and_run_performance_simulation(self, new_value):
        try:
            # generate the design
            self.modify_config_files(new_value)
            # TODO : Try to use Zinc to accelerate the process
            # clean_command = ["make", "clean"] 
            # subprocess.run(clean_command, cwd = self.generation_path, check=True)
            run_configure_command = ["make", "-j12", "CONFIG=CustomisedRocketConfig"]
            subprocess.run(run_configure_command, cwd = self.generation_path, check=True)
            performance_results = {}
            for benchmark_to_examine in self.cpu_info.supported_output_objs.benchmark.metrics:
                run_benchmark_command = ["make", "run-binary", "CONFIG=CustomisedRocketConfig", f"BINARY=../../toolchains/riscv-tools/riscv-tests/build/benchmarks/{benchmark_to_examine}.riscv"]
                
                try:
                    with open(self.processor_generation_log + benchmark_to_examine + '.log', 'w') as f:
                        subprocess.run(run_benchmark_command, check=True, stdout=f, stderr=f, cwd=self.generation_path)
                    performance_results[benchmark_to_examine] = self.extract_metrics_from_log(True, benchmark_to_examine)
                    print("<---------------------->")
                    print(benchmark_to_examine)
                    print(performance_results[benchmark_to_examine])
                except subprocess.CalledProcessError as e:
                    print(f"Error occurred for the current benchmark {benchmark_to_examine}")
                    performance_results[benchmark_to_examine] = self.extract_metrics_from_log(False, benchmark_to_examine)
            if len(performance_results) == 0:
                return False, None
            return True, performance_results
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred: {e}")
            return False, None
    def build_new_processor(self, new_config):
        try:
            self.modify_config_files(new_config)
            run_configure_command = ["make", "-j12", "CONFIG=CustomisedRocketConfig"]
            subprocess.run(run_configure_command, cwd = self.generation_path, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            return False
    



if __name__ == '__main__':
    pass