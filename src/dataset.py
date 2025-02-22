import sqlite3
from sampler import Sampler
import processor_analyser
import json
import time

def create_table_from_json(cpu_info, dataset_direct):
    """Create a table in the database based on a JSON file."""
    # Start building the CREATE TABLE command
    dataset_name = f"{cpu_info.cpu_name}_PPA"
    sql_command = f"CREATE TABLE IF NOT EXISTS {dataset_name} (\n"
    # sql_command += "    config_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"

    # Add Configurable Parameters to the table
    for param in cpu_info.config_params.params:
        if param.param_type == "int":
            sql_command += f"    {param.name} INTEGER,\n"
        elif param.param_type == "categorical":
            sql_command += f"    {param.name} TEXT,\n"
    # Output Params
    ## 1. Power
    for metric in cpu_info.supported_output_objs.power.metrics:
        sql_command += f"    Power_{metric} FLOAT,\n"
    ## 2. Resource_Utilisation
    for metric in cpu_info.supported_output_objs.resource.metrics:
        sql_command += f"    Resource_Utilisation_{metric} FLOAT,\n"
    ## 3. Timing
    for metric in cpu_info.supported_output_objs.timing.metrics:
        sql_command += f"    Timing_{metric} FLOAT,\n"
    ## 4. Benchmark Performance
    for metric in cpu_info.supported_output_objs.benchmark.metrics:
        tmp_benchmark_metric = metric.replace("-", "_")
        for benchmark_criterion in ["exe_time", "throughput", "mcycles", "minstret"]:
            sql_command += f"    Benchmark_{tmp_benchmark_metric}_{benchmark_criterion} INTEGER,\n"
    
    ## Validity Fail, Partial, Success
    sql_command += "    Evaluation VARCHAR(7),\n"
    
    ## Define the Primary Key
    sql_command += "    PRIMARY KEY ("
    for param in cpu_info.config_params.params:
        sql_command += f" {param.name},"

    # Remove the last comma and add closing parenthesis
    sql_command = sql_command.rstrip(',') + '  ) \n)'
    # Connect to the SQLite database and execute the command
    try:
        conn = sqlite3.connect(dataset_direct)
        cursor = conn.cursor()
        cursor.execute(sql_command)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    return sql_command


class Processor_Dataset:
    def __init__(self, cpu_info, fpga_info=None):
        self.cpu_info = cpu_info
        self.fpga_considered = (fpga_info != None)
        self.fpga_info = fpga_info
        self.dataset_name = f"{self.cpu_info.cpu_name}_PPA"
        self.dataset_directory = f'../dataset/PPA/{self.dataset_name}.db'
        temp_data_index = 0
        self.resource_utilisation_indexes = []
        self.target_obj_indexes = []
        # Create Tuner Object
        self.tuner = processor_analyser.get_chip_tuner(cpu_info)
        # Create Sampler
        self.sampler = Sampler(cpu_info)

        # Prepare Insertion Command
        self.insert_command = f"INSERT INTO {self.dataset_name} ( "
        for param in self.cpu_info.config_params.params:
            self.insert_command += f"{param.name},\n"
            temp_data_index += 1
        # Output Params

        ## 1. Power
        for metric in self.cpu_info.supported_output_objs.power.metrics:
            self.insert_command += f"Power_{metric},\n"
            temp_data_index += 1

        ## 2. Resource_Utilisation
        for metric in self.cpu_info.supported_output_objs.resource.metrics:
            self.insert_command += f"Resource_Utilisation_{metric},\n"
            self.resource_utilisation_indexes.append(temp_data_index)
            temp_data_index += 1

        ## 3. Timing
        for metric in self.cpu_info.supported_output_objs.timing.metrics:
            self.insert_command += f"Timing_{metric},\n"
            temp_data_index += 1    
        
        ## 4. Benchmark Performance
        for metric in self.cpu_info.supported_output_objs.benchmark.metrics:
            tmp_benchmark_metric = metric.replace("-", "_")
            for benchmark_criterion in ["exe_time", "throughput", "mcycles", "minstret"]:
                self.insert_command += f"    Benchmark_{tmp_benchmark_metric}_{benchmark_criterion},\n"
            # This is for evaluation purposes
            for target_benchmark in self.cpu_info.target_benchmark:
                if target_benchmark.name == metric:
                    for benchmark_criterion in ["exe_time", "throughput", "mcycles", "minstret"]:
                        if target_benchmark.activated_benchmark_metric[benchmark_criterion] == True:
                            self.target_obj_indexes.append(temp_data_index)
                        temp_data_index += 1
                else:
                    temp_data_index += 4
        if len(self.target_obj_indexes) == 0:
            raise Exception("No target objectives found.")
        self.insert_command += "Evaluation)"
        self.insert_command = self.insert_command + 'VALUES ('
        for i in range(self.cpu_info.config_params.amount + self.cpu_info.supported_output_objs.metric_amounts + 1):
            self.insert_command += '?, '
        self.insert_command = self.insert_command.rstrip(', ') + ')'
        # Prepare Fetch Command
        self.fetch_command = f"SELECT * FROM {self.dataset_name} WHERE "
        for i, param in enumerate(self.cpu_info.config_params.params):
            if i == 0:
                self.fetch_command += f"{param.name} = ? "
            else:
                self.fetch_command += f"AND {param.name} = ? "

        # Prepare Default Parameter Setting List
        self.default_params = []
        for param in self.cpu_info.config_params.params:
            self.default_params.append(param.default_value)

        if self.fpga_considered:
            self.fpga_info.update_rc_data_indexes(self.resource_utilisation_indexes)
        
        # Prepare delete command
        self.delete_command = f"DELETE FROM {self.dataset_name} WHERE "
        for i, param in enumerate(self.cpu_info.config_params.params):
            if i == 0:
                self.delete_command += f"{param.name} = ? "
            else:
                self.delete_command += f"AND {param.name} = ? "
        
    def insert_to_dataset(self, data):
        """Insert data into the database, only used during the sampling stage"""
        try:
            conn = sqlite3.connect(self.dataset_directory)
            cursor = conn.cursor()
            cursor.execute(self.insert_command, data)
            conn.commit()
            conn.close() 
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
    
    def preheat_dataset(self):
        while True:
            next_sample = self.sampler.find_next_sample('oat')
            if len(next_sample) == 0:
                print("Complete initialisation")
                break
            print(f"Next Sample: {next_sample}")
            validity, _, _ = self.fetch_single_data_acc_to_def_from_dataset(next_sample)
            if validity:
                self.sampler.mark_sample_complete(next_sample)
            else:
                print("Skipping the sample.")

    
    def conduct_experiments(self, config_params):
        """Conduct experiments based on the configuration parameters"""
        # Performance Simulation  
        print(f"Starting the performance simulation with the Config{config_params}") 
        design_validity, performance_results = self.tuner.tune_and_run_performance_simulation(config_params)
        if design_validity == "Fail":
            return [-1] * self.cpu_info.supported_output_objs.metric_amounts, design_validity
        # Synthesis
        synthesis_validity = self.tuner.run_synthesis(config_params)
        if synthesis_validity == False:
            design_validity = "Fail"
            return [-1] * self.cpu_info.supported_output_objs.metric_amounts, design_validity

        utilisation_results = self.tuner.parse_vivado_resource_utilisation_report()
        print("Utilisation Results")
        print(utilisation_results)
        power_results = self.tuner.parse_vivado_power_report()
        print("Power Results")
        print(power_results)
        timing_results= self.tuner.parse_vivado_timing_report()
        print("Timing Results")
        print(timing_results)
        results = []
        
        for power in self.cpu_info.supported_output_objs.power.metrics:
            if power_results[power] == None:
                results.append(-1)
            else:
                results.append(power_results[power])
        
        for utilisation in self.cpu_info.supported_output_objs.resource.metrics:
            if utilisation_results[utilisation] == None:
                results.append(-1)
            else:
                results.append(utilisation_results[utilisation])
        
        for timing in self.cpu_info.supported_output_objs.timing.metrics:
            if timing_results[timing] == None:
                results.append(-1)
            else:
                results.append(timing_results[timing])
        for benchmark in self.cpu_info.supported_output_objs.benchmark.metrics:
            for benchmark_criterion in ["exe_time", "throughput", "mcycles", "minstret"]:
                if performance_results[benchmark][benchmark_criterion] == None:
                    results.append(-1)
                else:
                    results.append(performance_results[benchmark][benchmark_criterion])
                
        return results, design_validity

    def query_dataset(self, data_input):
        config_to_fetch = self.default_params.copy()
        print("default_params: ", self.default_params)
        for i in range(len(data_input)):
            if self.cpu_info.config_params.params[self.cpu_info.tunable_params_index[i]].param_type == "int":
                config_to_fetch[self.cpu_info.tunable_params_index[i]] = int(data_input[i])
            elif self.cpu_info.config_params.params[self.cpu_info.tunable_params_index[i]].param_type == "categorical": # Here we assume the input is string.
                assert (data_input[i] in self.cpu_info.config_params.params[self.cpu_info.tunable_params_index[i]].self_range), f"Invalid input: {data_input[i]} for {self.cpu_info.config_params.params[self.cpu_info.tunable_params_index[i]].name}"
                config_to_fetch[self.cpu_info.tunable_params_index[i]] = data_input[i]

        return self.fetch_single_data_acc_to_def_from_dataset(config_to_fetch)


    def query_fake_data(self, data_input):
        # Note, its just for debugging purposes
        return True, True, [-1 for i in range(len(self.target_obj_indexes))], [-1 for i in range(len(self.resource_utilisation_indexes))]

    def fetch_single_data_acc_to_def_from_dataset(self, data_to_fetch):
        """Fetch data based on certain input values and outputs the FPGA_Deployability True/False, Objectives }"""
        # Output (Validity of the data, FPGA Deployability, Target Objectives, RC_results)
        
        results = []
        try:
            conn = sqlite3.connect(self.dataset_directory)
            # Create a cursor object and execute the SQL command
            cursor = conn.cursor()
            cursor.execute(self.fetch_command, data_to_fetch)
            # Fetch all results from the cursor
            rows = cursor.fetchall()
            if len(rows) == 0:
                print("No data found in the database. Conducting experiments...")
                print(data_to_fetch)
                results, experiment_validity = self.conduct_experiments(data_to_fetch)
                data_to_insert = data_to_fetch + results + [experiment_validity]
                print("Data to insert: \n", data_to_insert)
                self.insert_to_dataset(data_to_insert)
                rc_results = [data_to_insert[i] for i in self.resource_utilisation_indexes]
                target_obj_results = [data_to_insert[i] for i in self.target_obj_indexes]
            else:
                if rows[0][-1] == 'Success' or rows[0][-1] == 'Partial':
                    rc_results = [rows[0][i] for i in self.resource_utilisation_indexes]
                    target_obj_results = [rows[0][i] for i in self.target_obj_indexes]
                else:
                    print("The data is invalid.")
                    return False, False, None, None
            if  self.fpga_considered:
                return True, self.fpga_info.check_fpga_deployability(rc_results), target_obj_results, rc_results
            else:
                return True, True, target_obj_results, rc_results          
            
        except sqlite3.Error as e:
            Exception(f"An error occurred: {e}")
            quit()
            return False, False, None, None
    

    def design_space_exploration(self):
        """Explore the design space by iteratively querying the dataset."""
        while True:
            next_sample = self.sampler.find_next_sample('default')
            if len(next_sample) == 0:
                print("All samples have been evaluated.")
                break
            print(f"Next Sample: {next_sample}")
            # self.delete_data_from_dataset(next_sample)
            validity, _, _, _ = self.fetch_single_data_acc_to_def_from_dataset(next_sample)
            if validity:
                self.sampler.mark_sample_complete(next_sample)
            else:
                print("Skipping the sample.")
    
    def delete_data_from_dataset(self, data_input):
        try:
            conn = sqlite3.connect(self.dataset_directory)
            cursor = conn.cursor()
            cursor.execute(self.delete_command, data_input)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")

    def debug_print(self):
        print("Insert Command is ")
        print(self.insert_command)
        print("Fetch Command is ")
        print(self.fetch_command)
        print("Default Params")
        print(self.default_params)
        print("Resource Indexes")
        print(self.resource_utilisation_indexes)
        print("Objective Indexes")
        print(self.target_obj_indexes)
    
    def debug_visualise_db(self):
        try:
            conn = sqlite3.connect(self.dataset_directory)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.dataset_name}")
            rows = cursor.fetchall()
            # Fetch column names
            column_names = [description[0] for description in cursor.description]
            
            # Display column names and rows
            print(f"\nContents of table: {self.dataset_name}")
            print(" | ".join(column_names))
            print("-" * 50)
            for row in rows:
                for i in range(len(row)):
                    print(row[i], end="    |   ")
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
    
    def modify_dataset(self, column_name, default_value):
        # Add a new column to the dataset
        sql_command = f"ALTER TABLE {self.dataset_name} ADD COLUMN new_column_name {column_name} DEFAULT {default_value}"
        try:
            conn = sqlite3.connect(self.dataset_directory)
            cursor = conn.cursor()
            cursor.execute(sql_command)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
    

    def run_evaluation_experiment(self):
        # Run the evaluation experiment
        testcase_file_dir = f"../experiments/evaluation_speed_results/random_{self.cpu_info.cpu_name.lower()}_designs.json"
        evaluation_results_dir = f"../experiments/evaluation_speed_results/evaluation_results_{self.cpu_info.cpu_name.lower()}.json"
        with open(testcase_file_dir, 'r') as file:
            testcases = json.load(file)

        # Load existing results if the file exists, otherwise start with an empty dictionary
        try:
            with open(evaluation_results_dir, 'r') as file:
                all_results = json.load(file)
        except FileNotFoundError:
            all_results = {}
        # Process each test case
        for config_index in testcases.keys():
            # Skip if the result for the current config_index already exists
            if config_index in all_results:
                print(f"Skipping config_index {config_index}: already processed.")
                continue

            start_time = time.time()
            validity, fpga_deployability, target_obj_results, rc_results = self.fetch_single_data_acc_to_def_from_dataset(list(testcases[config_index].values()))
            end_time = time.time()
            time_taken = end_time - start_time

            print(f"Validity: {validity}, FPGA Deployability: {fpga_deployability}, Target Objectives: {target_obj_results}, RC Results: {rc_results}, Time Taken: {time_taken:.6f}")

            # Append new results for the current configuration index
            all_results[config_index] = {
                "Validity": validity,
                "FPGA Deployability": fpga_deployability,
                "Target Objectives": target_obj_results,
                "RC Results": rc_results,
                "Time Taken": time_taken
            }
            # Write updated results back to the file after each experiment
            with open(evaluation_results_dir, 'w') as file:
                json.dump(all_results, file, indent=4)
        print("Evaluation results updated successfully.")

def view_dataset():
    proc_name = input("Enter the processor name: ")
    dataset_directory = f'dataset/PPA/{proc_name}_PPA.db'
    try:
        conn = sqlite3.connect(dataset_directory)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {proc_name}_PPA")
        rows = cursor.fetchall()
        # Fetch column names
        column_names = [description[0] for description in cursor.description]
        
        # Display column names and rows
        print(f"\nContents of table: {proc_name}")
        print(" | ".join(column_names))
        print("-" * 50)
        for row in rows:
            for i in range(len(row)):
                print(row[i], end="    |   ")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")


def view_specified_dataset():
    # Ask the user for the processor name and the column name
    proc_name = input("Enter the processor name: ")
    column_name = input("Enter the column name you want to view: ")

    # Prepare the database path
    dataset_directory = f'dataset/PPA/{proc_name}_PPA.db'

    try:
        # Connect to the database
        conn = sqlite3.connect(dataset_directory)
        cursor = conn.cursor()

        # Fetch only the specified column from the table
        query = f"SELECT {column_name} FROM {proc_name}_PPA"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Display the results
        print(f"\nContents of column '{column_name}' from table '{proc_name}_PPA':\n")
        for row in rows:
            print(row[0])  # Each row is a tuple, so row[0] is the column value

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    # view_dataset()
    view_specified_dataset()