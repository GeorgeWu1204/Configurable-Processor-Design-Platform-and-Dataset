import pandas as pd

# Load the Excel file
file_path = 'device_sheet.xlsx'  # Update with the actual path to your file
df = pd.read_excel(file_path)

# Convert the DataFrame to a JSON file
json_path = 'fpga_rc.json'
df.to_json(json_path, orient='records', indent=4)

print(f"Data saved to {json_path}")
