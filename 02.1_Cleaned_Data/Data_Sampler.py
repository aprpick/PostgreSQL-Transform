import os
import csv
import math

script_dir = os.path.dirname(os.path.abspath(__file__))
print("Script directory:", script_dir)

samples_dir = os.path.join(script_dir, 'Samples')
os.makedirs(samples_dir, exist_ok=True)
print("Created Samples folder at:", samples_dir)

csv_files = [f for f in os.listdir(script_dir) if f.lower().endswith('.csv')]
if not csv_files:
    print("No CSV files found in script directory.")
else:
    for file in csv_files:
        print("Processing:", file)
        full_path = os.path.join(script_dir, file)
        sample_path = os.path.join(samples_dir, f'sample_{file}')
        
        with open(full_path, 'r', newline='') as f:
            reader = csv.reader(f)
            total_rows = sum(1 for _ in reader)
        total_data_rows = total_rows - 1 if total_rows > 0 else 0
        print("Total data rows:", total_data_rows)
        
        if total_data_rows == 0:
            continue
        
        if total_data_rows <= 100:
            indices = set(range(total_data_rows))
        else:
            indices = set(round(i * total_data_rows / 99) for i in range(100))
        
        with open(full_path, 'r', newline='') as f_in, open(sample_path, 'w', newline='') as f_out:
            reader = csv.reader(f_in)
            writer = csv.writer(f_out)
            row_num = 0
            for row in reader:
                if row_num == 0:
                    writer.writerow(row)
                elif (row_num - 1) in indices:
                    writer.writerow(row)
                row_num += 1
            print("Created sample:", sample_path)