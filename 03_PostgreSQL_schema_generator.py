"""
Phase 3: PostgreSQL Schema Generator
Analyzes cleaned CSVs and generates optimized PostgreSQL schema with DDL
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import math
from typing import Dict, Any, Tuple


# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).parent
CLEANED_DATA = PROJECT_ROOT / "02.1_Cleaned_Data"
SCHEMA_FILE = PROJECT_ROOT / "01.1_PostgreSQL_Schema.json"
DESCRIPTIONS_FILE = PROJECT_ROOT / "00_Raw_Data" / "00_column_descriptions.json"

OUTPUT_SCHEMA = PROJECT_ROOT / "03.1_PostgreSQL_Schema.json"
OUTPUT_DDL = PROJECT_ROOT / "03.1_PostgreSQL_DDL.sql"
OUTPUT_REPORT = PROJECT_ROOT / "03.1_Optimization_Report.md"


# --- HELPER FUNCTIONS ---
def load_json(filepath):
    """Load JSON file"""
    if Path(filepath).exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def analyze_code_column(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """Analyze a CODE column (string identifiers)"""
    non_null = df[col].dropna().astype(str)
    
    if len(non_null) == 0:
        return {
            'postgres_type': 'VARCHAR(50)',
            'nullable': True,
            'min_length': 0,
            'max_length': 0,
            'avg_length': 0,
            'reason': 'All NULL values, defaulting to VARCHAR(50)'
        }
    
    lengths = non_null.str.len()
    min_length = int(lengths.min())
    max_length = int(lengths.max())
    avg_length = float(round(lengths.mean(), 1))
    has_nulls = bool(df[col].isna().any())
    
    # Add 20% headroom, round up to nearest 5
    recommended_length = math.ceil(max_length * 1.2 / 5) * 5
    recommended_length = max(recommended_length, max_length + 2)  # At least +2
    
    return {
        'postgres_type': f'VARCHAR({recommended_length})',
        'nullable': has_nulls,
        'min_length': min_length,
        'max_length': max_length,
        'avg_length': avg_length,
        'recommended_length': recommended_length,
        'reason': f'Max length {max_length}, rounded to VARCHAR({recommended_length})'
    }


def analyze_numeric_int_column(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """Analyze a NUMERIC column (Int64 - integers)"""
    non_null = df[col].dropna()
    
    if len(non_null) == 0:
        return {
            'postgres_type': 'INTEGER',
            'nullable': True,
            'min_value': None,
            'max_value': None,
            'reason': 'All NULL values, defaulting to INTEGER'
        }
    
    min_val = int(non_null.min())
    max_val = int(non_null.max())
    has_nulls = bool(df[col].isna().any())
    
    # PostgreSQL integer type ranges
    SMALLINT_MIN, SMALLINT_MAX = -32768, 32767
    INTEGER_MIN, INTEGER_MAX = -2147483648, 2147483647
    
    # Conservative limits: use only 50% of SMALLINT, 25% of INTEGER to leave room for future growth
    SMALLINT_SAFE = 16000  # ~50% of 32,767
    INTEGER_SAFE = 500000000  # ~25% of 2,147,483,647 (500 million)
    
    # Determine type
    if min_val >= SMALLINT_MIN and max_val <= SMALLINT_SAFE:
        pg_type = 'SMALLINT'
        reason = f'Range {min_val:,} to {max_val:,} fits in SMALLINT (max {SMALLINT_SAFE:,})'
    elif min_val >= INTEGER_MIN and max_val <= INTEGER_SAFE:
        pg_type = 'INTEGER'
        reason = f'Range {min_val:,} to {max_val:,} fits in INTEGER (max {INTEGER_SAFE:,})'
    else:
        pg_type = 'BIGINT'
        reason = f'Range {min_val:,} to {max_val:,} requires BIGINT for future growth'
    
    return {
        'postgres_type': pg_type,
        'nullable': has_nulls,
        'min_value': min_val,
        'max_value': max_val,
        'reason': reason
    }


def analyze_numeric_float_column(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """Analyze a NUMERIC column (Float64 - decimals)"""
    non_null = df[col].dropna()
    
    if len(non_null) == 0:
        return {
            'postgres_type': 'NUMERIC(10,2)',
            'nullable': True,
            'min_value': None,
            'max_value': None,
            'reason': 'All NULL values, defaulting to NUMERIC(10,2)'
        }
    
    min_val = float(non_null.min())
    max_val = float(non_null.max())
    has_nulls = bool(df[col].isna().any())
    
    # Determine max decimal places by checking all non-null values
    # For large datasets, check if any value has decimals (efficient)
    max_decimals = 0
    
    # First, quick check: are all values whole numbers?
    all_whole = (non_null == non_null.astype(int)).all()
    
    if not all_whole:
        # Some values have decimals - find max decimal places
        for val in non_null.sample(min(10000, len(non_null))):  # Sample up to 10k for performance
            if pd.notna(val):
                # Convert to string and check decimal places
                str_val = f"{val:.10f}".rstrip('0').rstrip('.')
                if '.' in str_val:
                    decimals = len(str_val.split('.')[1])
                    max_decimals = max(max_decimals, decimals)
    
    # If max_decimals is 0, treat as integer (nullable Int64 that went through CSV)
    if max_decimals == 0:
        # This is actually an integer that became float64 due to CSV round-trip
        min_int = int(min_val)
        max_int = int(max_val)
        
        # Use same logic as analyze_numeric_int_column
        SMALLINT_SAFE = 16000
        INTEGER_SAFE = 500000000
        
        if min_int >= -32768 and max_int <= SMALLINT_SAFE:
            pg_type = 'SMALLINT'
            reason = f'Range {min_int:,} to {max_int:,} fits in SMALLINT (max {SMALLINT_SAFE:,})'
        elif min_int >= -2147483648 and max_int <= INTEGER_SAFE:
            pg_type = 'INTEGER'
            reason = f'Range {min_int:,} to {max_int:,} fits in INTEGER (max {INTEGER_SAFE:,})'
        else:
            pg_type = 'BIGINT'
            reason = f'Range {min_int:,} to {max_int:,} requires BIGINT for future growth'
        
        return {
            'postgres_type': pg_type,
            'nullable': has_nulls,
            'min_value': min_int,
            'max_value': max_int,
            'reason': reason
        }
    
    # Has actual decimals - use NUMERIC(precision, scale)
    # Determine total digits needed
    max_abs = max(abs(min_val), abs(max_val))
    if max_abs == 0:
        integer_digits = 1
    else:
        integer_digits = math.floor(math.log10(abs(max_abs))) + 1
    
    # Add headroom
    precision = integer_digits + max_decimals + 2
    scale = max_decimals
    
    # PostgreSQL max precision is 131072, but practical limit
    precision = min(precision, 38)
    
    return {
        'postgres_type': f'NUMERIC({precision},{scale})',
        'nullable': has_nulls,
        'min_value': min_val,
        'max_value': max_val,
        'precision': precision,
        'scale': scale,
        'reason': f'Max {max_decimals} decimal places, range {min_val:.4f} to {max_val:.4f}'
    }


def analyze_text_column(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """Analyze a TEXT column"""
    non_null = df[col].dropna().astype(str)
    
    if len(non_null) == 0:
        return {
            'postgres_type': 'TEXT',
            'nullable': True,
            'min_length': 0,
            'max_length': 0,
            'avg_length': 0.0,
            'reason': 'All NULL values'
        }
    
    # Filter out empty strings for length analysis
    non_empty = non_null[non_null.str.len() > 0]
    
    if len(non_empty) == 0:
        return {
            'postgres_type': 'TEXT',
            'nullable': True,
            'min_length': 0,
            'max_length': 0,
            'avg_length': 0.0,
            'reason': 'All empty or NULL values'
        }
    
    lengths = non_empty.str.len()
    min_length = int(lengths.min())
    max_length = int(lengths.max())
    avg_length = float(round(lengths.mean(), 1))
    
    # Check for NULLs or empty strings
    has_nulls = bool(df[col].isna().any() or (df[col].astype(str).str.len() == 0).any())
    
    # Decide VARCHAR vs TEXT
    # Use VARCHAR if max_length is reasonable and consistent
    if max_length <= 255 and (max_length - min_length) / max(max_length, 1) < 0.5:
        # Consistent length, use VARCHAR with headroom
        recommended_length = math.ceil(max_length * 1.2 / 5) * 5
        recommended_length = max(recommended_length, max_length + 2)
        pg_type = f'VARCHAR({recommended_length})'
        reason = f'Consistent length (max {max_length}), using VARCHAR'
    else:
        # Variable length or very long, use TEXT
        pg_type = 'TEXT'
        reason = f'Variable length (min {min_length}, max {max_length}), using TEXT'
    
    return {
        'postgres_type': pg_type,
        'nullable': has_nulls,
        'min_length': min_length,
        'max_length': max_length,
        'avg_length': avg_length,
        'reason': reason
    }


def analyze_boolean_column(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """Analyze a BOOLEAN column (Int64 with 0/1)"""
    has_nulls = bool(df[col].isna().any())
    
    return {
        'postgres_type': 'BOOLEAN',
        'nullable': has_nulls,
        'reason': 'Boolean column (0/1)'
    }


def analyze_date_column(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """Analyze a DATE column (object with DD/MM/YYYY strings)"""
    has_nulls = bool(df[col].isna().any())
    
    return {
        'postgres_type': 'DATE',
        'nullable': has_nulls,
        'reason': 'Date column (DD/MM/YYYY format)'
    }


def sanitize_table_name(filename: str) -> str:
    """Convert CSV filename to valid PostgreSQL table name"""
    # Remove .csv extension
    name = filename.replace('.csv', '')
    
    # Remove Cleaned_ prefix if present
    if name.startswith('Cleaned_'):
        name = name[8:]
    
    # Remove leading numbers and underscores (e.g., "01_")
    import re
    name = re.sub(r'^[\d_]+', '', name)
    
    # Replace special characters with underscores
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove trailing underscores
    name = name.strip('_')
    
    return name


def generate_ddl(table_name: str, columns: Dict[str, Dict], descriptions: Dict = None) -> str:
    """Generate PostgreSQL CREATE TABLE DDL"""
    ddl_lines = [f"CREATE TABLE {table_name} ("]
    
    col_definitions = []
    for col_name, col_info in columns.items():
        pg_type = col_info['postgres_type']
        nullable = ' NULL' if col_info.get('nullable', True) else ' NOT NULL'
        
        # Add column comment if description available
        col_def = f"    {col_name} {pg_type}{nullable}"
        col_definitions.append(col_def)
    
    ddl_lines.append(',\n'.join(col_definitions))
    ddl_lines.append(");")
    
    # Add column comments if descriptions available
    if descriptions:
        ddl_lines.append("")
        for col_name, desc in descriptions.items():
            if col_name in columns:
                safe_desc = desc.replace("'", "''")  # Escape single quotes
                ddl_lines.append(f"COMMENT ON COLUMN {table_name}.{col_name} IS '{safe_desc}';")
    
    return '\n'.join(ddl_lines)


# --- MAIN PROCESSING ---
def main():
    print("=" * 70)
    print("PHASE 3: POSTGRESQL SCHEMA GENERATOR")
    print("=" * 70)
    
    # Load schema and descriptions
    schema = load_json(SCHEMA_FILE)
    all_descriptions = load_json(DESCRIPTIONS_FILE)
    
    # Initialize outputs
    postgres_schema = {}
    ddl_statements = []
    report_lines = [
        "# PostgreSQL Schema Optimization Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    # Process each cleaned CSV
    csv_files = sorted(CLEANED_DATA.glob("Cleaned_*.csv"))
    
    for csv_file in csv_files:
        csv_name = csv_file.name.replace('Cleaned_', '')
        
        # Skip if not in schema
        if csv_name not in schema:
            print(f"⚠️  Skipping {csv_name} (not in schema)")
            continue
        
        print(f"\n📊 Analyzing: {csv_name}")
        report_lines.append(f"## {csv_name}")
        report_lines.append("")
        
        # Load CSV
        df = pd.read_csv(csv_file, low_memory=False)
        print(f"  Loaded {len(df):,} rows")
        
        # Get column schema
        col_schema = schema[csv_name]
        
        # Generate table name
        table_name = sanitize_table_name(csv_name)
        print(f"  Table name: {table_name}")
        report_lines.append(f"**Table Name:** `{table_name}`")
        report_lines.append(f"**Rows Analyzed:** {len(df):,}")
        report_lines.append("")
        
        # Analyze each column
        columns_info = {}
        
        report_lines.append("| Column | Type | Strip Actions | PostgreSQL Type | Nullable | Analysis |")
        report_lines.append("|--------|------|---------------|-----------------|----------|----------|")
        
        for col_name in df.columns:
            if col_name not in col_schema:
                continue
            
            col_config = col_schema[col_name]
            col_type = col_config.get('type')
            actions = col_config.get('actions', {})
            
            print(f"  🔍 {col_name} ({col_type})")
            
            # Analyze based on type
            if col_type == 'CODE':
                analysis = analyze_code_column(df, col_name)
            elif col_type == 'NUMERIC':
                # Check if Int64 or Float64
                dtype_str = str(df[col_name].dtype).lower()
                # Check for any integer type (Int64, int64, Int32, etc.)
                if 'int' in dtype_str and 'float' not in dtype_str:
                    analysis = analyze_numeric_int_column(df, col_name)
                else:  # Float64 or other float types
                    analysis = analyze_numeric_float_column(df, col_name)
            elif col_type == 'TEXT':
                analysis = analyze_text_column(df, col_name)
            elif col_type == 'BOOLEAN':
                analysis = analyze_boolean_column(df, col_name)
            elif col_type == 'DATE':
                analysis = analyze_date_column(df, col_name)
            else:
                continue
            
            columns_info[col_name] = analysis
            
            # Build strip actions display
            action_badges = []
            if actions.get('nonnumeric'):
                action_badges.append('[$,%]')
            if actions.get('decimal'):
                action_badges.append('[.00]')
            if actions.get('leading_zeros') and col_type == 'NUMERIC':
                action_badges.append('[0...]')
            
            strip_actions_display = ' '.join(action_badges) if action_badges else '-'
            
            # Add to report
            nullable_display = 'Yes' if analysis.get('nullable', True) else 'No'
            report_lines.append(
                f"| {col_name} | {col_type} | {strip_actions_display} | {analysis['postgres_type']} | "
                f"{nullable_display} | {analysis['reason']} |"
            )
        
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # Store in postgres schema
        postgres_schema[csv_name] = {
            'table_name': table_name,
            'columns': columns_info
        }
        
        # Generate DDL
        descriptions = all_descriptions.get(csv_name, {})
        ddl = generate_ddl(table_name, columns_info, descriptions)
        ddl_statements.append(f"-- Table: {table_name}")
        ddl_statements.append(f"-- Source: {csv_name}")
        ddl_statements.append(ddl)
        ddl_statements.append("")
        
        print(f"  ✅ Analysis complete")
    
    # Save PostgreSQL schema JSON
    with open(OUTPUT_SCHEMA, 'w', encoding='utf-8') as f:
        json.dump(postgres_schema, f, indent=2)
    print(f"\n💾 Saved schema: {OUTPUT_SCHEMA}")
    
    # Save DDL
    with open(OUTPUT_DDL, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ddl_statements))
    print(f"💾 Saved DDL: {OUTPUT_DDL}")
    
    # Save report
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f"💾 Saved report: {OUTPUT_REPORT}")
    
    print("=" * 70)
    print("✅ SCHEMA GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()