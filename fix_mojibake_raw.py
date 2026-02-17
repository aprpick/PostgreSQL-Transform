import pandas as pd
from pathlib import Path

# Fix mojibake in cleaned CSV files
CLEANED_DATA = Path(__file__).parent / "02.1_Cleaned_Data"

csv_files = list(CLEANED_DATA.glob("*.csv"))

for csv_file in csv_files:
    print(f"Fixing {csv_file.name}...")
    
    # Read the cleaned file
    df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False)
    
    # Fix mojibake in all object columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(
            lambda x: x.replace('â€œ', '"')
                       .replace('â€', '"')
                       .replace('â€™', "'")
                       .replace('â€"', '-')
                       .replace('â€"', '-')
            if isinstance(x, str) else x
        )
    
    # Save back with UTF-8
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"  ✅ Fixed {csv_file.name}")

print("\nAll cleaned files fixed!")