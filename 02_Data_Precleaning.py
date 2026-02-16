import pandas as pd
from pathlib import Path
import json
import re
from datetime import datetime

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).parent

# INPUTS
RAW_DATA = PROJECT_ROOT / "00_Raw_Data"                          # Raw CSV files
SCHEMA_FILE = PROJECT_ROOT / "01.1_PostgreSQL_Schema.json"       # From Script 01

# OUTPUTS
CLEANED_DATA = PROJECT_ROOT / "02.1_Cleaned_Data"                # Cleaned CSV files
REPORT_FILE = PROJECT_ROOT / "02.1_Cleaning_Report.md"           # Cleaning report



# Create output directory
CLEANED_DATA.mkdir(exist_ok=True)

# --- HELPER FUNCTIONS ---
def load_schema():
    """Load schema JSON"""
    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def strip_nonnumeric(value):
    """Remove non-numeric characters except - (if no numbers before it) and ."""
    if pd.isna(value):
        return value
    
    str_val = str(value).strip()
    
    # Check if there's a - that should be preserved (no digits before it)
    has_leading_negative = False
    for char in str_val:
        if char == '-':
            has_leading_negative = True
            break
        elif char.isdigit():
            break  # Found digit before -, don't preserve
    
    # Remove all non-numeric except decimal point
    cleaned = re.sub(r'[^0-9.]', '', str_val)
    
    # Add back negative sign if appropriate
    if has_leading_negative and cleaned:
        cleaned = '-' + cleaned
    
    return cleaned if cleaned else value

def strip_decimal(value):
    """Remove .00 or .0 but keep significant decimals like 0.5"""
    if pd.isna(value):
        return value
    
    str_val = str(value).strip()
    
    # Only strip if ends with .0 or .00 (or more zeros)
    if '.' in str_val:
        parts = str_val.split('.')
        if len(parts) == 2:
            # Check if decimal part is all zeros
            if parts[1] and all(c == '0' for c in parts[1]):
                return parts[0]  # Return just the integer part
    
    return str_val

def strip_leading_zeros(value):
    """Remove leading zeros but preserve decimals like 0.5"""
    if pd.isna(value):
        return value
    
    str_val = str(value).strip()
    
    # If it starts with 0. then keep it (decimal number)
    if str_val.startswith('0.'):
        return str_val
    
    # If it starts with -0. then keep it (negative decimal)
    if str_val.startswith('-0.'):
        return str_val
    
    # Otherwise strip leading zeros
    # Handle negative numbers
    if str_val.startswith('-'):
        return '-' + str_val[1:].lstrip('0') or '0'
    else:
        return str_val.lstrip('0') or '0'

def clean_numeric(value, actions):
    """Apply numeric cleaning actions and convert to proper numeric type"""
    if pd.isna(value):
        return pd.NA  # Use pandas NA instead of NaN
    
    result = value
    
    # Apply actions in order
    if actions.get('nonnumeric', False):
        result = strip_nonnumeric(result)
    
    if actions.get('decimal', False):
        result = strip_decimal(result)
    
    if actions.get('leading_zeros', False):
        result = strip_leading_zeros(result)
    
    # Convert to proper numeric type
    try:
        # If has decimal point, return as float
        if '.' in str(result):
            return float(result)
        else:
            return int(result)
    except (ValueError, TypeError):
        return pd.NA  # Return NA if conversion fails

def clean_boolean(value, actions):
    """Map boolean values to 1/0 as integers"""
    if pd.isna(value):
        return value
    
    str_val = str(value).strip()
    true_value = actions.get('true_value', 'True')
    false_value = actions.get('false_value', 'False')
    
    if str_val == true_value:
        return int(1)
    elif str_val == false_value:
        return int(0)
    else:
        return value  # Keep as-is if doesn't match

def clean_date(value, actions):
    """Parse and reformat dates"""
    if pd.isna(value):
        return value
    
    str_val = str(value).strip()
    
    # Get format info
    input_format = actions.get('input_format', 'Auto-detect')
    output_format = actions.get('output_format', 'DD/MM/YYYY')
    
    # Map display names to Python strftime codes
    format_map = {
        'YYYY-MM-DD': '%Y-%m-%d',
        'MM/DD/YYYY': '%m/%d/%Y',
        'DD/MM/YYYY': '%d/%m/%Y',
        'Month DD, YYYY': '%B %d, %Y',
        'Mon DD, YYYY': '%b %d, %Y',
        'DD Month YYYY': '%d %B %Y',
    }
    
    # Try to parse
    parsed_date = None
    
    if input_format == 'Auto-detect':
        # Try common formats
        for fmt_name, fmt_code in format_map.items():
            try:
                parsed_date = datetime.strptime(str_val, fmt_code)
                break
            except:
                continue
    else:
        # Use specified format
        fmt_code = format_map.get(input_format, '%Y-%m-%d')
        try:
            parsed_date = datetime.strptime(str_val, fmt_code)
        except:
            return value  # Return original if can't parse
    
    if parsed_date is None:
        return value  # Couldn't parse
    
    # Format output
    if output_format == 'Keep original':
        return value
    
    output_fmt = format_map.get(output_format, '%d/%m/%Y')
    return parsed_date.strftime(output_fmt)

def clean_text(value):
    """Strip whitespace from text"""
    if pd.isna(value):
        return value
    return str(value).strip()

# --- MAIN PROCESSING ---
def main():
    print("=" * 60)
    print("01.5 - DATA PRECLEANING")
    print("=" * 60)
    
    # Load schema
    schema = load_schema()
    
    # Initialize report
    report_lines = [
        "# Data Precleaning Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    # Process each CSV
    csv_files = sorted([f for f in RAW_DATA.glob("*.csv")])
    
    for csv_file in csv_files:
        csv_name = csv_file.name
        
        # Skip if not in schema
        if csv_name not in schema:
            print(f"⚠️  Skipping {csv_name} (not in schema)")
            continue
        
        print(f"\n📄 Processing: {csv_name}")
        report_lines.append(f"## {csv_name}")
        report_lines.append("")
        
        # Load CSV
        try:
            df = pd.read_csv(csv_file, low_memory=False, encoding='utf-8')
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            print(f"  ⚠️  UTF-8 failed, trying latin-1 encoding...")
            df = pd.read_csv(csv_file, low_memory=False, encoding='latin-1')
        original_rows = len(df)
        print(f"  Loaded {original_rows:,} rows")
        
        # Get column schema
        col_schema = schema[csv_name]
        
        # Track changes for report
        changes = {}
        
        # Process each column
        for col_name in df.columns:
            if col_name not in col_schema:
                print(f"  ⚠️  Column '{col_name}' not in schema, keeping as-is")
                continue
            
            col_config = col_schema[col_name]
            col_type = col_config.get('type')
            actions = col_config.get('actions', {})
            
            # Skip IGNORE columns
            if col_type == 'IGNORE':
                print(f"  🚫 Dropping: {col_name} (IGNORE)")
                df.drop(columns=[col_name], inplace=True)
                changes[col_name] = {'type': 'IGNORE', 'action': 'Dropped column'}
                continue
            
            print(f"  🔧 Cleaning: {col_name} ({col_type})")
            
            # Collect before/after examples
            examples = []
            
            # Apply cleaning based on type
            if col_type == 'NUMERIC':
                for idx in df.index[:5]:  # Get first 5 examples
                    before = df.loc[idx, col_name]
                    after = clean_numeric(before, actions)
                    if str(before) != str(after):
                        examples.append((before, after))
                
                df[col_name] = df[col_name].apply(lambda x: clean_numeric(x, actions))
                
                # Convert to nullable Int64 or Float64
                try:
                    # Check if any values have decimals
                    has_decimals = df[col_name].apply(lambda x: isinstance(x, float) and not pd.isna(x)).any()
                    
                    if has_decimals:
                        df[col_name] = df[col_name].astype('Float64')  # Nullable float
                    else:
                        df[col_name] = df[col_name].astype('Int64')  # Nullable integer
                except:
                    pass  # Keep as-is if conversion fails
                
                # Build action description
                action_desc = []
                if actions.get('nonnumeric'): action_desc.append('strip non-numeric')
                if actions.get('decimal'): action_desc.append('strip decimal')
                if actions.get('leading_zeros'): action_desc.append('strip leading zeros')
                
                changes[col_name] = {
                    'type': col_type,
                    'actions': ', '.join(action_desc) if action_desc else 'none',
                    'examples': examples[:3]
                }
            
            elif col_type == 'CODE':
                # Codes are numeric identifiers that preserve leading zeros
                for idx in df.index[:5]:
                    before = df.loc[idx, col_name]
                    # Apply stripping but keep as string
                    after = str(before) if not pd.isna(before) else before
                    if actions.get('nonnumeric'):
                        after = strip_nonnumeric(after)
                    if actions.get('decimal'):
                        after = strip_decimal(after)
                    after = clean_text(after)  # Strip whitespace
                    
                    if str(before) != str(after):
                        examples.append((before, after))
                
                # Apply cleaning
                def clean_code(value):
                    if pd.isna(value):
                        return value
                    result = str(value)
                    if actions.get('nonnumeric'):
                        result = strip_nonnumeric(result)
                    if actions.get('decimal'):
                        result = strip_decimal(result)
                    return clean_text(result)  # Strip whitespace
                
                df[col_name] = df[col_name].apply(clean_code)
                df[col_name] = df[col_name].astype('object')  # Keep as string
                
                # Build action description
                action_desc = []
                if actions.get('nonnumeric'): action_desc.append('strip non-numeric')
                if actions.get('decimal'): action_desc.append('strip decimal')
                action_desc.append('keep as string')
                
                changes[col_name] = {
                    'type': col_type,
                    'actions': ', '.join(action_desc),
                    'examples': examples[:3]
                }
            
            elif col_type == 'BOOLEAN':
                for idx in df.index[:5]:
                    before = df.loc[idx, col_name]
                    after = clean_boolean(before, actions)
                    if str(before) != str(after):
                        examples.append((before, after))
                
                df[col_name] = df[col_name].apply(lambda x: clean_boolean(x, actions))
                
                # Convert to nullable Int64
                df[col_name] = df[col_name].astype('Int64')
                
                changes[col_name] = {
                    'type': col_type,
                    'actions': f"map {actions.get('true_value')}→1, {actions.get('false_value')}→0",
                    'examples': examples[:3]
                }
            
            elif col_type == 'DATE':
                for idx in df.index[:5]:
                    before = df.loc[idx, col_name]
                    after = clean_date(before, actions)
                    if str(before) != str(after):
                        examples.append((before, after))
                
                df[col_name] = df[col_name].apply(lambda x: clean_date(x, actions))
                
                changes[col_name] = {
                    'type': col_type,
                    'actions': f"format: {actions.get('output_format', 'DD/MM/YYYY')}",
                    'examples': examples[:3]
                }
            
            elif col_type == 'TEXT':
                df[col_name] = df[col_name].apply(clean_text)
                changes[col_name] = {
                    'type': col_type,
                    'actions': 'strip whitespace',
                    'examples': []
                }
        
        # Save cleaned CSV
        output_file = CLEANED_DATA / f"Cleaned_{csv_name}"
        df.to_csv(output_file, index=False)
        print(f"  ✅ Saved: {output_file} ({len(df):,} rows)")
        
        # Add to report
        report_lines.append(f"**Rows:** {original_rows:,}")
        report_lines.append("")
        
        # Add dtype summary
        report_lines.append("**Column Types After Cleaning:**")
        report_lines.append("")
        report_lines.append("| Column | Expected Type | Actions | Actual Dtype | Status |")
        report_lines.append("|--------|---------------|---------|--------------|--------|")
        
        for col_name in df.columns:
            if col_name in col_schema:
                expected_type = col_schema[col_name].get('type')
                actions = col_schema[col_name].get('actions', {})
                actual_dtype = str(df[col_name].dtype)
                
                # Build actions display
                action_badges = []
                if actions.get('nonnumeric'):
                    action_badges.append('[$,%]')
                if actions.get('decimal'):
                    action_badges.append('[.00]')
                if actions.get('leading_zeros') and expected_type == 'NUMERIC':
                    action_badges.append('[0s]')
                
                actions_display = ' '.join(action_badges) if action_badges else '-'
                
                # Check if dtype matches expected
                if expected_type == 'NUMERIC':
                    # If strip decimal is enabled, should be Int64
                    if actions.get('decimal', False):
                        if 'Int64' in actual_dtype:
                            status = '✅'
                        elif 'Float64' in actual_dtype or 'float' in actual_dtype.lower():
                            status = '⚠️ Expected Int64 (decimal stripped)'
                        elif 'int' in actual_dtype.lower():
                            status = '✅'
                        else:
                            status = '❌'
                    else:
                        # Decimal not stripped, Int64 or Float64 both OK
                        status = '✅' if 'int' in actual_dtype.lower() or 'float' in actual_dtype.lower() else '❌'
                elif expected_type == 'CODE':
                    # CODE should always be object (string)
                    status = '✅' if 'object' in actual_dtype or 'string' in actual_dtype.lower() else '❌'
                elif expected_type == 'BOOLEAN':
                    status = '✅' if 'int' in actual_dtype.lower() else '❌'
                elif expected_type == 'TEXT' or expected_type == 'DATE':
                    status = '✅' if 'object' in actual_dtype or 'string' in actual_dtype.lower() else '⚠️'
                else:
                    status = '-'
                
                report_lines.append(f"| {col_name} | {expected_type} | {actions_display} | {actual_dtype} | {status} |")
        
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # Detailed changes per column
        report_lines.append("### Detailed Changes")
        report_lines.append("")
        
        for col_name, change_info in changes.items():
            if change_info.get('action') == 'Dropped column':
                report_lines.append(f"### ❌ {col_name}")
                report_lines.append(f"**Action:** Dropped (IGNORE type)")
            else:
                report_lines.append(f"### {col_name} ({change_info['type']})")
                report_lines.append(f"**Actions:** {change_info['actions']}")
                
                if change_info['examples']:
                    report_lines.append(f"**Examples:**")
                    for before, after in change_info['examples']:
                        report_lines.append(f"- `{before}` → `{after}`")
            
            report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("")
    
    # Save report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\n📊 Report saved: {REPORT_FILE}")
    print("=" * 60)
    print("✅ PRECLEANING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()