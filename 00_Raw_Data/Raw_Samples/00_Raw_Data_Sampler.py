import pandas as pd
from pathlib import Path
import os

# Paths
SCRIPT_DIR = Path(__file__).parent
RAW_DATA = SCRIPT_DIR.parent
SAMPLES_DIR = SCRIPT_DIR

# Create Samples directory if it doesn't exist
SAMPLES_DIR.mkdir(exist_ok=True)

def sample_csv(file_path, sample_size=1000):
    """Sample rows from CSV spread evenly throughout the file"""
    print(f"Sampling {file_path.name}...")
    
    # First, count total rows quickly by reading just one column
    total_rows = sum(1 for _ in open(file_path, encoding='utf-8', errors='ignore')) - 1  # Subtract header
    
    if total_rows <= sample_size:
        # Small file, just load it all
        print(f"  File has only {total_rows} rows, loading all")
        return pd.read_csv(file_path, encoding='utf-8', encoding_errors='ignore')
    
    # Calculate which rows to keep (evenly spaced)
    skip_interval = total_rows / sample_size
    rows_to_keep = [int(i * skip_interval) for i in range(sample_size)]
    
    # Create skip function - keep rows in our list, skip all others
    rows_to_keep_set = set(rows_to_keep)
    skip_func = lambda x: x > 0 and x not in rows_to_keep_set  # x > 0 to keep header
    
    # Read with skiprows
    df = pd.read_csv(file_path, skiprows=skip_func, encoding='utf-8', encoding_errors='ignore')
    
    print(f"  Sampled {len(df)} rows from {total_rows} total")
    return df

def main():
    print(f"Looking for CSVs in: {RAW_DATA}")
    print(f"Saving samples to: {SAMPLES_DIR}\n")
    
    # Get all CSV files
    csv_files = list(RAW_DATA.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {RAW_DATA}")
        return
    
    print(f"Found {len(csv_files)} CSV file(s)\n")
    
    for csv_file in csv_files:
        try:
            # Sample the CSV
            sample_df = sample_csv(csv_file, sample_size=1000)
            
            # Create output filename with Sample_ prefix
            output_name = f"Sample_{csv_file.name}"
            output_path = SAMPLES_DIR / output_name
            
            # Save sample
            sample_df.to_csv(output_path, index=False, encoding='utf-8')
            
            print(f"  ✓ Created {output_name} ({len(sample_df)} rows)")
        
        except Exception as e:
            print(f"  ✗ Error processing {csv_file.name}: {e}")
    
    print(f"\nDone! Samples saved to: {SAMPLES_DIR}")

if __name__ == "__main__":
    main()