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
        self.top_level_design_name = "RocketTile"
        self.processor_config_matcher = config_matcher(cpu_info, self.top_level_design_name)


    def modify_custom_cpu(self, n):
        with open(self.cpu_level_config_file, 'r') as file:
            lines = file.readlines()
        pattern = re.compile(r'new freechips\.rocketchip\.rocket\.WithCustomisedCore\(\d+\)')
        for i, line in enumerate(lines):
            if 'class CustomisedRocketConfig' in line:
                for j in range(i+1, len(lines)):
                    if pattern.search(lines[j]):
                        lines[j] = pattern.sub(f'new freechips.rocketchip.rocket.WithCustomisedCore({n})', lines[j])
                        break
                break
        with open(self.cpu_level_config_file, 'w') as file:
            file.writelines(lines)

    def modify_custom_core_internal_config(self, input_vals):
            params_name = list(self.cpu_info.config_params.params_map.keys())[1:]
            print(params_name)
            print(input_vals)
            with open(self.core_level_configuration_file, 'r') as file:
                scala_code = file.read()
            
            # Regular expression to find the WithCustomisedCore class definition
            class_pattern = re.compile(
                    r'class\s+WithCustomisedCore\(\s*n:\s*Int,\s*crossing:\s*RocketCrossingParams\s*=\s*RocketCrossingParams\(\s*\),\s*\)\s*extends\s*Config\(\(site,\s*here,\s*up\)\s*=>\s*{\s*(.*?)\s*}\)',
                    re.DOTALL)

            match = class_pattern.search(scala_code)

            if match:
                print("WithCustomisedCore class definition found.")
                config_body = match.group(1)  # Corrected to match the single capture group
                for var_name, var_val in zip(params_name, input_vals):
                    print(var_name, var_val)
                    class_name, sub_name = var_name.split('_')
                    if class_name == 'icache':
                        pattern = re.compile(rf'icache\s*=\s*Some\(ICacheParams\((.*?)\)\)', re.DOTALL)
                        cache_match = pattern.search(config_body)
                    elif class_name == 'dcache':
                        pattern = re.compile(rf'dcache\s*=\s*Some\(DCacheParams\((.*?)\)\)', re.DOTALL)
                        cache_match = pattern.search(config_body)
                    if cache_match:
                        params = cache_match.group(1)
                        sub_pattern = re.compile(rf'{sub_name}\s*=\s*\d+')
                        if sub_pattern.search(params):
                            new_params = sub_pattern.sub(f'{sub_name} = {var_val}', params)
                            new_cache_body = cache_match.group(0).replace(params, new_params)
                            config_body = config_body.replace(cache_match.group(0), new_cache_body)
                        else:
                            print(f"{sub_name} not found in {class_name} parameters.")
                    else:
                        print(f"{class_name} class not found in the body.")
                
                # Rewrite the modified block back into the scala_code
                scala_code = class_pattern.sub(f'class WithCustomisedCore(\n  n: Int,\n  crossing: RocketCrossingParams = RocketCrossingParams(),\n) extends Config((site, here, up) => {{\n{config_body}}})', scala_code)

                with open(self.core_level_configuration_file, 'w') as file:
                    file.write(scala_code)
            else:
                print("WithCustomisedCore class definition not found.")

    def modify_config_files(self, input_vals):
        # CPU's overall configuration, Only modify the number of Cores
        self.modify_custom_cpu(input_vals[0])
        # Core's internal configuration
        self.modify_custom_core_internal_config(input_vals[1:])

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
    



if __name__ == '__main__':
    pass
    # from interface import define_cpu_settings
    # cpu_info, fpga_info = define_cpu_settings()
    # rocket_chip_tuner = Rocket_Chip_Tuner(cpu_info)
    # rocket_chip_tuner.modify_custom_cpu(3)