import re
import subprocess
import os
from processor_config_matching import config_matcher
from GeneralChip import General_Chip_Tuner


class EL2_VeeR_Tuner(General_Chip_Tuner):
    """This is the tuner for EL2 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, cpu_info):
        super().__init__(cpu_info)
        self.generation_path = '../processors/chipyard/sims/verilator'
        self.cpu_level_config_file = '../processors/chipyard/generators/chipyard/src/main/scala/config/BoomConfigs.scala'
        self.core_level_configuration_file = '../processors/chipyard/generators/boom/src/main/scala/v3/common/config-mixins.scala'
        self.top_level_design_name = "EL2"
        self.processor_config_matcher = config_matcher(cpu_info, self.top_level_design_name)

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
    


