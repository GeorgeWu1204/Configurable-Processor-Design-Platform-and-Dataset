import sqlite3
import json


def create_database(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS dataset
                 (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)''')
    conn.commit()
    conn.close()

def create_table_from_json(json_file):
    # Load JSON data
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Start building the CREATE TABLE command
    table_name = "processor_configs"
    sql_command = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    sql_command += "    config_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"

    # Add columns based on JSON keys and expected types
    for key, value in data.items():
        if key == "CPU_Name":
            sql_command += f"    {key} TEXT,\n"
        elif isinstance(value, dict) and 'self_range' in value:
            sql_command += f"    {key} INTEGER,\n"
        elif isinstance(value, list):
            sql_command += f"    {key} INTEGER,\n"

    # Remove the last comma and add closing parenthesis
    sql_command = sql_command.rstrip(',\n') + '\n)'

    # Connect to the SQLite database and execute the command
    conn = sqlite3.connect('processors.db')
    cursor = conn.cursor()
    cursor.execute(sql_command)
    conn.commit()
    conn.close()

    return sql_command


def insert_data(conn, data):
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO processor_data (clock_speed, cache_size, core_count, thread_count, architecture,
        execution_time, power_consumption, cpu_usage, memory_usage, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['clock_speed'], data['cache_size'], data['core_count'], data['thread_count'],
          data['architecture'], data['execution_time'], data['power_consumption'],
          data['cpu_usage'], data['memory_usage'], data['timestamp']))
    conn.commit()


