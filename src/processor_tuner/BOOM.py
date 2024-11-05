import re
import subprocess
from processor_config_matching import config_matcher
from GeneralChip import General_Chip_Tuner




class BOOM_Chip_Tuner(General_Chip_Tuner):

    def __init__(self, cpu_info):
        super().__init__(cpu_info)
        # Log file for the generated reports
        self.generation_path = '../processors/chipyard/sims/verilator'
        self.cpu_level_config_file = '../processors/chipyard/generators/chipyard/src/main/scala/config/BoomConfigs.scala'
        self.core_level_configuration_file = '../processors/chipyard/generators/boom/src/main/scala/v3/common/config-mixins.scala'
        self.top_level_design_name = "ChipTop"
        self.processor_config_matcher = config_matcher(cpu_info, self.top_level_design_name)
        
    
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
        params_name = list(self.cpu_info.config_params.params_map.keys())[1:]
        
        with open(self.core_level_configuration_file, 'r') as file:
            lines = file.readlines()

        new_lines = []
        in_custom_boom_class = False  # Flag to check if within the correct class block
        cache_context = None  # Track whether we're inside a dcache or icache block

        for line in lines:
            # Check for start of WithNCustomBooms class
            if line.strip().startswith('class WithNCustomBooms'):
                in_custom_boom_class = True
            elif line.strip().startswith('class') and 'WithNCustomBooms' not in line:
                in_custom_boom_class = False  # Exit block when a new class definition starts

            if in_custom_boom_class:
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
                            modified_line = pattern.sub(r'\g<1>' + str(value), modified_line)  # Replace with new value
                else:
                    for param, value in zip(params_name, input_vals):
                        if not ('dcache' in param or 'icache' in param):
                            core_param_pattern = re.compile(rf'(\b{re.escape(param)}\s*=\s*)(\d+)')
                            modified_line = core_param_pattern.sub(r'\g<1>' + str(value), modified_line)  # Replace with new value

                new_lines.append(modified_line)
            else:
                new_lines.append(line)  # Keep lines outside WithNCustomBooms class unchanged

        with open(self.core_level_configuration_file, 'w') as file:
            file.writelines(new_lines)

    def modify_config_files(self, input_vals):
        # CPU's overall configuration, Only modify the number of Cores
        self.modify_custom_cpu(input_vals[0])
        # Core's internal configuration
        self.modify_custom_core_internal_config(input_vals[1:])

    def extract_metrics_from_log(self, train_validity):
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
        if not train_validity:
            return metrics
        try:
            # Open the log file
            with open(self.processor_generation_log, 'r') as file:
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
            print(f"Error: The file {self.processor_generation_log} does not exist.")
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
                
                try:
                    with open(self.processor_generation_log, 'w') as f:
                        subprocess.run(run_benchmark_command, check=True, stdout=f, stderr=f, cwd=self.generation_path)
                    performance_results[benchmark_to_examine] = self.extract_metrics_from_log(True)
                    print("<---------------------->")
                    print(benchmark_to_examine)
                    print(performance_results[benchmark_to_examine])
                except subprocess.CalledProcessError as e:
                    print(f"Error occurred for the current benchmark {benchmark_to_examine}")
                    performance_results[benchmark_to_examine] = self.extract_metrics_from_log(False)
            if len(performance_results) == 0:
                return False, None
            return True, performance_results
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred: {e}")
            return False, None
    
    
    



if __name__ == '__main__':

    # print(extract_wns('../processors/Logs/Syn_Report/BOOM_timing_synth.rpt'))
    pass