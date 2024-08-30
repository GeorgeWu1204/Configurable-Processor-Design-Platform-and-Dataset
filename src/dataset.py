import sqlite3
from utils import read_from_json

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


def insert_data(conn, dataset_name, data_names, data):
    """Insert data into the database."""
    cursor = conn.cursor()
    sql_command = f"INSERT INTO {dataset_name} ({data_names}) VALUES ("
    for i in range(len(data)):
        sql_command += f"?, "
    sql_command = sql_command.rstrip(', ') + ')'    
    try:
        cursor.execute(sql_command, data)
        conn.commit()
        conn.close() 
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if cursor:
            cursor.close()


def fetch_data_as_dict(conn, cpu_info, data_input):
    """Fetch data based on certain input values and return it as a list of dictionaries."""
    data_dicts = []
    try:
        # Prepare the SQL statement with placeholders for parameters
        sql_command = f"SELECT * FROM {cpu_info['name']} WHERE "
        sql_command += f"{cpu_info.cpu_name} = ? "
        for param in cpu_info.config_params:
            sql_command += f"AND {param.name} = ? "

        # Create a cursor object and execute the SQL command
        cursor = conn.cursor()
        cursor.execute(sql_command, data_input)

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
    # create_database('processors.db')
    # create_table_from_json('../dataset/constraints/RocketChip_Config.json', 'RocketChip_PPA', '../dataset/PPA/RocketChip_PPA.db')
    # conn = sqlite3.connect('../dataset/PPA/RocketChip_PPA.db')
    # data_values = ['RocketChip', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # columns = 'CPU_Name, icache_nSets, icache_nWays, dcache_nSets, dcache_nWays, nTLBSets, nTLBWays, Power_Dynamic, Power_Static, Resource_Utilisation_LUTs, Resource_Utilisation_FFs, Resource_Utilisation_BRAM, Resource_Utilisation_DSP, Benchmark_Dhrystone, Benchmark_CoreMark, Benchmark_Whetstone'
    # # Call the function to insert data
    # insert_data(conn, 'RocketChip_PPA', columns, data_values)
    cpu_info = read_from_json('../dataset/constraints/RocketChip_Config.json')
    create_table_from_json(cpu_info, '../dataset/PPA/RocketChip_PPA.db')