# PostgreSQL Data Transformation Pipeline

A complete Python-based pipeline for cleaning, categorizing, and loading CSV data into PostgreSQL with optimized schema generation.

## Overview

This pipeline transforms raw CSV files into a PostgreSQL database with optimized data types and comprehensive data cleaning. It handles millions of rows efficiently and provides detailed reports at every stage.

**Total Processing Capacity:** 14.7+ million rows across 4 tables

## Pipeline Flow

```
Raw CSVs → Script 01 (Categorize) → Script 02 (Clean) → Script 03 (Generate Schema) → PostgreSQL
```

## Project Structure

```
PostgreSQL_Transform/
├── 00_Raw_Data/                    # INPUT: Raw CSV files
│   └── 00_column_descriptions.json # Optional: Column descriptions
├── 01_PostgreSQL_Schema_Categorizer.py  # Script 01: Categorize columns (Streamlit)
├── 02_Data_Precleaning.py          # Script 02: Clean data
├── 03_PostgreSQL_Schema_Generator.py    # Script 03: Generate PostgreSQL schema
├── 01.1_PostgreSQL_Schema.json     # OUTPUT: Column categorization
├── 02.1_Cleaned_Data/              # OUTPUT: Cleaned CSV files
├── 02.1_Cleaning_Report.md         # OUTPUT: Cleaning report
├── 03.1_PostgreSQL_Schema.json     # OUTPUT: PostgreSQL schema details
├── 03.1_PostgreSQL_DDL.sql         # OUTPUT: CREATE TABLE statements
└── 03.1_Optimization_Report.md     # OUTPUT: Schema optimization report
```

## Requirements

### Software

* Python 3.8+
* PostgreSQL 14+
* pgAdmin 4 (optional, for viewing data)

### Python Packages

```bash
pip install pandas streamlit openpyxl python-docx
```

**Or use requirements.txt:**

```txt
pandas>=2.0.0
streamlit>=1.28.0
openpyxl>=3.1.0
python-docx>=1.1.0
```

Install with:

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Prepare Your Data

Place raw CSV files in `00_Raw_Data/` folder.

**Optional:** Create `00_column_descriptions.json` for column documentation:

```json
{
  "your_file.csv": {
    "column_name": "Description of what this column contains",
    "another_column": "Another description"
  }
}
```

### 2. Run Script 01: Column Categorization (Interactive)

**Launch Streamlit interface:**

```bash
streamlit run 01_PostgreSQL_Schema_Categorizer.py
```

**In the web interface:**

1. Select a CSV file from the dropdown
2. For each column, choose a type:
   * **CODE** - Identifiers (ZIP codes, PINs) - preserves leading zeros
   * **NUMERIC** - Numbers for math - strips leading zeros
   * **TEXT** - Strings, names
   * **BOOLEAN** - True/false values
   * **DATE** - Dates (will be formatted as DD/MM/YYYY)
   * **IGNORE** - Drop this column
3. Set stripping actions:
   * Strip non-numeric ($, %, commas)
   * Strip decimals (.00)
   * Strip leading zeros (NUMERIC only)
4. Click "Save Schema"
5. Repeat for all CSV files

**Output:** `01.1_PostgreSQL_Schema.json`

### 3. Run Script 02: Data Precleaning

**Clean the data based on your categorization:**

```bash
python 02_Data_Precleaning.py
```

**What it does:**

* Strips characters ($, %, commas) from numeric columns
* Removes decimals from integers
* Strips leading zeros from NUMERIC columns
* Preserves leading zeros in CODE columns (ZIP codes, IDs)
* Converts BOOLEAN columns (True→1, False→0)
* Formats dates as DD/MM/YYYY
* Drops IGNORE columns

**Outputs:**

* `02.1_Cleaned_Data/Cleaned_*.csv` - Cleaned CSV files
* `02.1_Cleaning_Report.md` - Detailed cleaning report with examples

### 4. Run Script 03: PostgreSQL Schema Generation

**Analyze cleaned data and generate optimized PostgreSQL schema:**

```bash
python 03_PostgreSQL_Schema_Generator.py
```

**What it does:**

* Analyzes actual data ranges
* Determines optimal PostgreSQL types:
  * CODE → VARCHAR(n) with headroom
  * NUMERIC integers → SMALLINT/INTEGER/BIGINT based on range
  * NUMERIC decimals → NUMERIC(precision, scale)
  * TEXT → VARCHAR(n) or TEXT based on consistency
  * BOOLEAN → BOOLEAN
  * DATE → DATE
* Generates CREATE TABLE statements with column comments

**Outputs:**

* `03.1_PostgreSQL_DDL.sql` - Ready-to-run SQL statements
* `03.1_PostgreSQL_Schema.json` - Detailed schema information
* `03.1_Optimization_Report.md` - Analysis report

### 5. Load into PostgreSQL

**Connect to PostgreSQL:**

```bash
psql -U postgres
```

**Create database and load data:**

```sql
-- Create database
CREATE DATABASE assessor_data;

-- Connect to it
\c assessor_data

-- Run DDL to create tables
\i 'C:/path/to/your/03.1_PostgreSQL_DDL.sql'

-- Set date format (for DD/MM/YYYY dates)
SET datestyle = 'DMY';

-- Load cleaned data
\COPY table_name FROM 'C:/path/to/02.1_Cleaned_Data/Cleaned_file.csv' CSV HEADER;

-- Repeat for each table
```

**Example load command:**

```sql
\COPY assessor_parcel_sales_2023_2025 
FROM 'C:/Documents-C/PostgresSQL_Transform/02.1_Cleaned_Data/Cleaned_01_Assessor_-_Parcel_Sales_2023_2025.csv' 
CSV HEADER;
```

### 6. Verify Data

**Check row counts:**

```sql
SELECT COUNT(*) FROM table_name;
```

**View sample data:**

```sql
SELECT * FROM table_name LIMIT 10;
```

**Or use pgAdmin:**

1. Open pgAdmin
2. Navigate to: Databases → assessor_data → Schemas → public → Tables
3. Right-click table → View/Edit Data → All Rows

## Data Types Explained

### CODE vs NUMERIC

**Use CODE for:**

* ZIP codes (60010, 07001)
* IDs, PINs (identifiers)
* Any numeric-looking data where leading zeros matter

**Use NUMERIC for:**

* Prices, amounts
* Counts, measurements
* Any number you'll do math on

**Key difference:** CODE preserves leading zeros, NUMERIC strips them.

### Type Mapping

| Input Type        | Cleaned dtype   | PostgreSQL Type         | Example            |
| ----------------- | --------------- | ----------------------- | ------------------ |
| CODE              | object (string) | VARCHAR(n)              | ZIP: "60010"       |
| NUMERIC (int)     | Int64           | SMALLINT/INTEGER/BIGINT | Price: 275000      |
| NUMERIC (decimal) | Float64         | NUMERIC(p,s)            | Rate: 0.5432       |
| TEXT              | object (string) | VARCHAR(n) or TEXT      | Name: "John Smith" |
| BOOLEAN           | Int64           | BOOLEAN                 | 0 or 1             |
| DATE              | object (string) | DATE                    | "25/01/2023"       |

## Safety Margins

The pipeline uses conservative safety margins to handle future data growth:

* **SMALLINT:** Uses only if max ≤ 16,000 (50% of 32,767 max)
* **INTEGER:** Uses only if max ≤ 500,000,000 (25% of 2.1B max)
* **BIGINT:** For anything larger
* **VARCHAR:** Adds 20% headroom, rounds to nearest 5

This ensures your schema won't break if data values increase over time.

## Configuration Files

### 01.1_PostgreSQL_Schema.json

**Structure:**

```json
{
  "filename.csv": {
    "column_name": {
      "type": "NUMERIC",
      "actions": {
        "nonnumeric": true,
        "decimal": true,
        "leading_zeros": true,
        "note": ""
      }
    }
  }
}
```

### 00_column_descriptions.json (Optional)

**Structure:**

```json
{
  "filename.csv": {
    "column_name": "Human-readable description"
  }
}
```

Descriptions are added as SQL comments in the DDL:

```sql
COMMENT ON COLUMN table_name.column_name IS 'Your description';
```

## Reports

### 02.1_Cleaning_Report.md

Shows for each file:

* Row count
* Column-by-column cleaning actions
* Before/after examples
* Data type verification

### 03.1_Optimization_Report.md

Shows for each table:

* Table name in PostgreSQL
* Total rows analyzed
* Column-by-column analysis:
  * Original type
  * Strip actions applied
  * Recommended PostgreSQL type
  * Nullable status
  * Min/max ranges or string lengths

## Troubleshooting

### "psql not recognized"

**Solution:** Add PostgreSQL bin to PATH:

```powershell
$env:PATH += ";C:\Program Files\PostgreSQL\18\bin"
```

### "Date/time field value out of range"

**Solution:** Set datestyle before loading:

```sql
SET datestyle = 'DMY';
```

### "Table name too long"

PostgreSQL truncates identifiers to 63 characters. The pipeline generates table names from filenames, so very long filenames will be truncated.

### Large file processing is slow

For files >1M rows, Script 03 samples data for decimal place analysis (first 1000 rows) but scans all rows for min/max values. This is normal and necessary for accurate schema generation.

## Performance

**Tested with:**

* 216,550 row file: ~5 seconds (Script 02), ~8 seconds (Script 03)
* 5,592,069 row file: ~45 seconds (Script 02), ~2 minutes (Script 03)
* 3,306,906 row file: ~30 seconds (Script 02), ~90 seconds (Script 03)

**Total:** Processing 14.7M rows takes approximately 5 minutes.

## CSV Limitations

**Important:** CSV files cannot preserve pandas Int64 dtype. Nullable integers become float64 when saved to CSV and reloaded. Script 03 detects this automatically:

1. If Float64 has 0 decimal places → treats as integer
2. Recommends SMALLINT/INTEGER/BIGINT accordingly

This is transparent to the user - the final PostgreSQL schema is correct.

## Reprocessing Data

To process updated CSV files:

1. Replace files in `00_Raw_Data/`
2. Re-run Script 02: `python 02_Data_Precleaning.py`
3. Re-run Script 03: `python 03_PostgreSQL_Schema_Generator.py`
4. Drop and recreate PostgreSQL database
5. Re-run DDL and COPY commands

**Note:** Schema (01.1_PostgreSQL_Schema.json) is reused - no need to recategorize unless columns changed.

## Advanced: PostgreSQL Optimization

After loading data, consider adding:

**Primary Keys:**

```sql
ALTER TABLE table_name ADD PRIMARY KEY (column1, column2);
```

**Indexes:**

```sql
CREATE INDEX idx_column ON table_name(column_name);
```

**Foreign Keys (if tables are related):**

```sql
ALTER TABLE child_table 
ADD FOREIGN KEY (pin) REFERENCES parent_table(pin);
```

## Example Dataset

This pipeline was tested on Cook County Assessor data:

* **Parcel Sales:** 216,550 property sales (2023-2025)
* **Parcel Addresses:** 5,592,069 property addresses
* **Assessed Values:** 5,592,069 tax assessments (2023-2025)
* **Property Characteristics:** 3,306,906 building details

**Total:** 14.7 million rows processed successfully.

## License

This pipeline is provided as-is for data transformation projects.

## Credits

Developed for transforming large CSV datasets into optimized PostgreSQL databases with comprehensive data cleaning and type optimization.
