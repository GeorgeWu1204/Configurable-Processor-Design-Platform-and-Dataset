import sqlite3

def create_table_from_json(cpu_info, dataset_direct):
    """Create a table in the database based on a JSON file."""

    # Start building the CREATE TABLE command
    dataset_name = f"{cpu_info.cpu_name}_PPA"
    sql_command = f"CREATE TABLE IF NOT EXISTS {dataset_name} (\n"
    sql_command += "    config_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
    sql_command += f"    {cpu_info.cpu_name} TEXT,\n"
    # Add Configurable Parameters to the table
    for param in cpu_info.config_params:
        sql_command += f"    {param.name} INTEGER,\n"
    for classification in cpu_info.output_params.keys():
        for metric in cpu_info.output_params[classification].metrics:
            sql_command += f"    {cpu_info.output_params[classification].class_name}_{metric} INTEGER,\n"
    # Remove the last comma and add closing parenthesis
    sql_command = sql_command.rstrip(',\n') + '\n)'
    # Connect to the SQLite database and execute the command
    try:
        conn = sqlite3.connect(dataset_direct)
        cursor = conn.cursor()
        cursor.execute(sql_command)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
    return sql_command


class Processor_Dataset:
    def __init__(self, cpu_info):
        self.cpu_info = cpu_info
        self.dataset_name = f"{self.cpu_info.cpu_name}_PPA"
        self.dataset_directory = f'../dataset/PPA/{self.dataset_name}.db'
        
        # Prepare Insertion Command
        self.insert_command = f"INSERT INTO {self.dataset_name} ( "
        for param in self.cpu_info.config_params:
            self.insert_command += f"{param.name}, "
        for classification in cpu_info.output_params.keys():
            for metric in self.cpu_info.output_params[classification].metrics:
                self.insert_command += f"{self.cpu_info.output_params[classification].class_name}_{metric}, "
        self.insert_command = self.insert_command.rstrip(', ') + ') VALUES ('
        for i in range(len(cpu_info.config_params)):
            self.insert_command += '?, '
        self.insert_command = self.insert_command.rstrip(', ') + ')'
        print(self.insert_command)

        # Prepare Fetch Command
        self.fetch_command = f"SELECT * FROM {self.dataset_name} WHERE "
        self.fetch_command += f"{cpu_info.cpu_name} = ? "
        for param in cpu_info.config_params:
            self.fetch_command += f"AND {param.name} = ? "
        
        # Prepare Default Parameter Setting List
        self.default_params = []
        for param in self.cpu_info.config_params:
            self.default_params.append(param.default_value)
        
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
        finally:
            if cursor:
                cursor.close()

    def fetch_single_data_as_dict(self, data_input):
        """Fetch data based on certain input values and return it as a list of dictionaries."""
        data_dicts = self.default_params
        for i in len(data_input):
            data_dicts[self.cpu_info.tunable_params[i]] = data_input[i]
        try:
            conn = sqlite3.connect(self.dataset_directory)
            # Create a cursor object and execute the SQL command
            cursor = conn.cursor()
            cursor.execute(self.fetch_command, data_input)
            # Fetch all results from the cursor
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            # Convert each row into a dictionary
            for row in rows:
                data_dicts.append(dict(zip(columns, row)))

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
            if cursor:
                cursor.close()

        return data_dicts

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