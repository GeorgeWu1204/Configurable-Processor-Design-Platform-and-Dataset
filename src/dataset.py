import sqlite3
from processor_tuning import Rocket_Chip_Tuner, BOOM_Chip_Tuner


def create_table_from_json(cpu_info, dataset_direct):
    """Create a table in the database based on a JSON file."""
    # Start building the CREATE TABLE command
    dataset_name = f"{cpu_info.cpu_name}_PPA"
    sql_command = f"CREATE TABLE IF NOT EXISTS {dataset_name} (\n"
    # sql_command += "    config_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"

    # Add Configurable Parameters to the table
    for param in cpu_info.config_params.params:
        sql_command += f"    {param.name} INTEGER,\n"
    # Output Params
    ## 1. Power
    for metric in cpu_info.supported_output_objs.power.metrics:
        sql_command += f"    Power_{metric} INTEGER,\n"
    ## 2. Resource_Utilisation
    for metric in cpu_info.supported_output_objs.resource.metrics:
        sql_command += f"    Resource_Utilisation_{metric} INTEGER,\n"
    ## 3. Benchmark Performance
    for metric in cpu_info.supported_output_objs.benchmark.metrics:
        tmp_benchmark_metric = metric.replace("-", "_")
        for benchmark_criterion in ["exe_time", "throughput", "mcycles", "minstret"]:
            sql_command += f"    Benchmark_{tmp_benchmark_metric}_{benchmark_criterion} INTEGER,\n"
    
    ## Define the Primary Key
    sql_command += "    PRIMARY KEY ("
    for param in cpu_info.config_params.params:
        sql_command += f" {param.name},"

    # Remove the last comma and add closing parenthesis
    sql_command = sql_command.rstrip(',') + '  ) \n)'
    print(sql_command)
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
    def __init__(self, cpu_info, fpga_info):
        self.cpu_info = cpu_info
        self.fpga_considered = (fpga_info != None)
        self.fpga_info = fpga_info
        self.dataset_name = f"{self.cpu_info.cpu_name}_PPA"
        self.dataset_directory = f'../dataset/PPA/{self.dataset_name}.db'
        temp_data_index = 0
        self.resource_utilisation_indexes = []
        self.target_obj_indexes = []
        tuner_list = {"RocketChip" : Rocket_Chip_Tuner, "BOOM" : BOOM_Chip_Tuner}
        self.tuner = tuner_list[self.cpu_info.cpu_name] (cpu_info)

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
            
        ## 3. Benchmark Performance
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

        self.insert_command = self.insert_command.rstrip(',\n') + ') VALUES ('
        for i in range(self.cpu_info.config_params.amount + self.cpu_info.supported_output_objs.metric_amounts):
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
        
    def insert_single_data(self, data):
        """Insert data into the database, only used during the sampling stage"""
        try:
            conn = sqlite3.connect(self.dataset_directory)
            cursor = conn.cursor()
            cursor.execute(self.insert_command, data)
            conn.commit()
            conn.close() 
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")

    def fetch_single_data_as_dict(self, data_input):
        """Fetch data based on certain input values and return it as a list of dictionaries."""
        data_to_fetch = self.default_params
        results = []
        for i in range(len(data_input)):
            data_to_fetch[self.cpu_info.tunable_params_index[i]] = data_input[i]
        try:
            conn = sqlite3.connect(self.dataset_directory)
            # Create a cursor object and execute the SQL command
            cursor = conn.cursor()
            cursor.execute(self.fetch_command, data_to_fetch)
            # Fetch all results from the cursor
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            # Convert each row into a dictionary
            for row in rows:
                results.append(dict(zip(columns, row)))

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")

        return results
    
    def fetch_single_data_acc_to_def(self, data_input):
        """Fetch data based on certain input values and outputs the FPGA_Deployability True/False, Objectives }"""
        data_to_fetch = self.default_params
        results = []
        for i in range(len(data_input)):
            data_to_fetch[self.cpu_info.tunable_params_index[i]] = data_input[i]
        try:
            conn = sqlite3.connect(self.dataset_directory)
            # Create a cursor object and execute the SQL command
            cursor = conn.cursor()
            cursor.execute(self.fetch_command, data_to_fetch)
            # Fetch all results from the cursor
            rows = cursor.fetchall()
            if len(rows) == 0:
                # TODO
                pass
                quit()
                
            rc_results = [rows[0][i] for i in self.resource_utilisation_indexes]
            target_obj_results = [rows[0][i] for i in self.target_obj_indexes]
            
            if  self.fpga_considered:
                return self.fpga_info.check_fpga_deployability(rc_results), target_obj_results            
            
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")

        return results
    
    
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





if __name__ == '__main__':
    pass
    # create_database('processors.db')
    # create_table_from_json('../dataset/constraints/RocketChip_Config.json', 'RocketChip_PPA', '../dataset/PPA/RocketChip_PPA.db')
    # conn = sqlite3.connect('../dataset/PPA/RocketChip_PPA.db')
    # data_values = ['RocketChip', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # columns = 'CPU_Name, icache_nSets, icache_nWays, dcache_nSets, dcache_nWays, nTLBSets, nTLBWays, Power_Dynamic, Power_Static, Resource_Utilisation_LUTs, Resource_Utilisation_FFs, Resource_Utilisation_BRAM, Resource_Utilisation_DSP, Benchmark_Dhrystone, Benchmark_CoreMark, Benchmark_Whetstone'
    # # Call the function to insert data
    # insert_data(conn, 'RocketChip_PPA', columns, data_values)
    # cpu_info = read_from_json('../dataset/constraints/RocketChip_Config.json')
    # create_table_from_json(cpu_info, '../dataset/PPA/RocketChip_PPA.db')