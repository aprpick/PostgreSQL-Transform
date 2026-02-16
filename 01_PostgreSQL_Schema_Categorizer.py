import streamlit as st
import pandas as pd
from pathlib import Path
import json
import os
from datetime import datetime
import random

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).parent

# INPUTS
RAW_DATA = PROJECT_ROOT / "00_Raw_Data"
DESCRIPTIONS_FILE = RAW_DATA / "00_column_descriptions.json"

# OUTPUT
SCHEMA_FILE = PROJECT_ROOT / "01.1_PostgreSQL_Schema.json"



# Sample settings
MAX_SAMPLE_SIZE = 10000  # Max rows to analyze
DISPLAY_SAMPLES = 60  # Samples to show in UI

st.set_page_config(layout="wide", page_title="Schema Categorizer")

# --- HELPER FUNCTIONS ---
def load_json(filepath):
    """Load JSON file"""
    if Path(filepath).exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_schema(schema):
    """Save schema to JSON"""
    with open(SCHEMA_FILE, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)

def save_column_type(file_name, col_name, col_type, actions=None):
    """Save a single column's type and actions immediately"""
    schema = load_json(SCHEMA_FILE)
    if file_name not in schema:
        schema[file_name] = {}
    
    # Always save the type and actions
    schema[file_name][col_name] = {'type': col_type}
    if actions:
        schema[file_name][col_name]['actions'] = actions
    
    save_schema(schema)

def sample_csv_with_seeking(csv_path, target_samples=10000):
    """Sample CSV by seeking to evenly-distributed positions"""
    # First, count total rows to avoid over-sampling
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        header_line = f.readline()
        total_rows = sum(1 for _ in f)
    
    # Don't sample more than what exists
    actual_samples = min(target_samples, total_rows)
    
    # Parse header
    columns = header_line.strip().split(',')
    columns = [col.strip('"') for col in columns]
    
    # If file is small enough, just read it all
    if actual_samples >= total_rows * 0.9:  # If sampling >90%, just read all
        df = pd.read_csv(csv_path, low_memory=False)
        samples = {col: df[col].dropna().astype(str).tolist() for col in df.columns}
        return columns, samples, total_rows
    
    # Otherwise, use seeking for larger files
    file_size = os.path.getsize(csv_path)
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        f.readline()  # Skip header
        header_end = f.tell()
    
    data_size = file_size - header_end
    
    # Generate seek positions
    positions = []
    for i in range(actual_samples):
        pos = header_end + int(i * data_size / actual_samples)
        positions.append(pos)
    
    # Collect samples by seeking
    samples = {col: [] for col in columns}
    
    with open(csv_path, 'rb') as f:
        for pos in positions:
            f.seek(pos)
            f.readline()  # Skip partial line
            line = f.readline().decode('utf-8', errors='ignore').strip()
            
            if not line:
                continue
            
            # Simple CSV parsing (handle quoted values)
            values = []
            current = []
            in_quotes = False
            
            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    values.append(''.join(current).strip('"'))
                    current = []
                else:
                    current.append(char)
            values.append(''.join(current).strip('"'))
            
            # Map to columns
            for i, col in enumerate(columns):
                if i < len(values):
                    val = values[i].strip()
                    if val and val.lower() not in ['', 'null', 'nan', 'none']:
                        samples[col].append(val)
    
    return columns, samples, actual_samples

def detect_date_format(samples):
    """Detect date format and count unparseable samples"""
    formats_to_try = [
        ('%Y-%m-%d', 'YYYY-MM-DD'),
        ('%m/%d/%Y', 'MM/DD/YYYY'),
        ('%d/%m/%Y', 'DD/MM/YYYY'),
        ('%Y/%m/%d', 'YYYY/MM/DD'),
        ('%m-%d-%Y', 'MM-DD-YYYY'),
        ('%d-%m-%Y', 'DD-MM-YYYY'),
        ('%Y%m%d', 'YYYYMMDD'),
        ('%B %d, %Y', 'Month DD, YYYY'),  # April 21, 2025
        ('%b %d, %Y', 'Mon DD, YYYY'),     # Apr 21, 2025
        ('%d %B %Y', 'DD Month YYYY'),     # 21 April 2025
        ('%d %b %Y', 'DD Mon YYYY'),       # 21 Apr 2025
        ('%m/%d/%y', 'MM/DD/YY'),
        ('%d/%m/%y', 'DD/MM/YY'),
    ]
    
    best_format = None
    best_parseable = 0
    best_name = 'Unknown'
    
    for fmt, name in formats_to_try:
        parseable = 0
        for sample in samples[:100]:  # Test first 100
            try:
                datetime.strptime(str(sample).strip(), fmt)
                parseable += 1
            except:
                pass
        
        if parseable > best_parseable:
            best_parseable = parseable
            best_format = fmt
            best_name = name
    
    # Calculate unparseable count for best format
    unparseable = 0
    if best_format:
        for sample in samples:
            try:
                datetime.strptime(str(sample).strip(), best_format)
            except:
                unparseable += 1
    else:
        unparseable = len(samples)
    
    return best_name, best_format, unparseable

def suggest_type(samples):
    """Suggest type based on sample values"""
    if len(samples) == 0:
        return 'TEXT'
    
    # Check for boolean patterns
    unique_values = set(str(s).lower().strip() for s in samples[:100])
    if len(unique_values) == 2:
        if unique_values <= {'true', 'false', 'yes', 'no', 'y', 'n', '1', '0', 't', 'f'}:
            return 'BOOLEAN'
    
    # Check if numeric
    numeric_count = 0
    for sample in samples[:100]:
        try:
            # Remove common formatting
            cleaned = str(sample).replace('$', '').replace(',', '').replace('%', '').strip()
            float(cleaned)
            numeric_count += 1
        except:
            pass
    
    if numeric_count / min(len(samples), 100) > 0.8:
        return 'NUMERIC'
    
    # Check if date
    date_name, date_fmt, unparseable = detect_date_format(samples[:100])
    if date_name != 'Unknown' and unparseable < len(samples[:100]) * 0.3:  # <30% unparseable
        return 'DATE'
    
    return 'TEXT'

# --- MAIN APP ---
def main():
    st.title("📋 PostgreSQL Schema Categorizer")
    st.markdown("**Step 1:** Categorize columns as NUMERIC, TEXT, DATE, BOOLEAN, or IGNORE")
    
    # Load schema and descriptions
    schema = load_json(SCHEMA_FILE)
    descriptions = load_json(DESCRIPTIONS_FILE)
    
    # Get CSV files
    csv_files = sorted([f.name for f in RAW_DATA.glob("*.csv")])
    
    if not csv_files:
        st.error(f"No CSV files found in {RAW_DATA}")
        return
    
    # Initialize selected file in session state
    if 'selected_file_idx' not in st.session_state:
        st.session_state.selected_file_idx = 0
    
    # File selector
    selected_file = st.selectbox(
        "📁 Select CSV File", 
        csv_files,
        index=st.session_state.selected_file_idx,
        key="file_selector"
    )
    
    # Update session state when selection changes
    st.session_state.selected_file_idx = csv_files.index(selected_file)
    
    if not selected_file:
        return
    
    csv_path = RAW_DATA / selected_file
    
    # Sample the CSV
    with st.spinner("Sampling CSV..."):
        columns, all_samples, total_sampled = sample_csv_with_seeking(csv_path, MAX_SAMPLE_SIZE)
    
    st.success(f"✅ Sampled {total_sampled:,} rows from CSV")
    
    # Get file descriptions
    file_descriptions = descriptions.get(selected_file, {})
    
    # Process each column
    for col_idx, col_name in enumerate(columns):
        st.markdown("---")
        
        # Get samples for this column
        col_samples = all_samples[col_name]
        
        # Get evenly-spaced display samples
        if len(col_samples) > 0:
            step = max(1, len(col_samples) // DISPLAY_SAMPLES)
            display_samples = col_samples[::step][:DISPLAY_SAMPLES]
        else:
            display_samples = []
        
        # Column header
        col_desc = file_descriptions.get(col_name, "No description")
        
        col_left, col_right = st.columns([2, 3])
        
        with col_left:
            st.markdown(f"### {col_name}")
            st.caption(col_desc)
            
            # Calculate stats
            unique_count = len(set(col_samples))
            null_count = total_sampled - len(col_samples)
            null_pct = (null_count / total_sampled * 100) if total_sampled > 0 else 0
            
            # Character length range
            if len(col_samples) > 0:
                lengths = [len(str(s)) for s in col_samples]
                min_len = min(lengths)
                max_len = max(lengths)
                length_ratio = max_len / min_len if min_len > 0 else 1
                
                # Color code based on ratio
                if length_ratio > 5:
                    length_color = "#ff0000"  # Red
                elif length_ratio > 3:
                    length_color = "#ff9900"  # Yellow/Orange
                else:
                    length_color = "#00cc00"  # Green
            else:
                min_len = max_len = 0
                length_color = "#00cc00"
            
            st.text(f"Samples analyzed: {total_sampled:,}")
            st.markdown(f"<span style='color: {length_color};'>Char length: {min_len}-{max_len}</span>", unsafe_allow_html=True)
            
            # Color code unique values (red if ≤2, gradient otherwise)
            if unique_count <= 2:
                unique_color = "#ff0000"
            elif unique_count < 10:
                unique_color = "#ff9900"
            else:
                unique_color = "#00cc00"
            st.markdown(f"<span style='color: {unique_color};'>Unique values: {unique_count:,}</span>", unsafe_allow_html=True)
            
            # Color code null % (red if >80%, gradient)
            if null_pct > 80:
                null_color = "#ff0000"
            elif null_pct > 50:
                null_color = "#ff6600"
            elif null_pct > 20:
                null_color = "#ff9900"
            else:
                null_color = "#00cc00"
            st.markdown(f"<span style='color: {null_color};'>Null/Empty: {null_count:,} ({null_pct:.1f}%)</span>", unsafe_allow_html=True)
            
            # Get current type
            current_schema = schema.get(selected_file, {}).get(col_name, {})
            current_type = current_schema.get('type', suggest_type(col_samples))
            
            # Type selector
            type_options = ['NUMERIC', 'CODE', 'TEXT', 'DATE', 'BOOLEAN', 'IGNORE']
            try:
                current_idx = type_options.index(current_type)
            except:
                current_idx = 2  # Default to TEXT
            
            selected_type = st.radio(
                "Type",
                type_options,
                index=current_idx,
                key=f"type_{selected_file}_{col_name}",
                horizontal=True
            )
            
            # Actions based on type
            actions = {}
            
            # Only load saved actions if type hasn't changed
            if selected_type == current_type:
                saved_actions = current_schema.get('actions', {})
            else:
                saved_actions = {}  # Reset actions when type changes
            
            if selected_type == 'NUMERIC':
                st.markdown("**Strip Actions:**")
                
                col_a1, col_a2, col_a3 = st.columns(3)
                with col_a1:
                    actions['nonnumeric'] = st.checkbox(
                        "Non-numeric",
                        value=saved_actions.get('nonnumeric', True),
                        key=f"strip_nn_{selected_file}_{col_name}",
                        help="Remove $, commas, %, etc."
                    )
                with col_a2:
                    actions['decimal'] = st.checkbox(
                        "Decimal",
                        value=saved_actions.get('decimal', True),
                        key=f"strip_dec_{selected_file}_{col_name}",
                        help="Remove .00"
                    )
                with col_a3:
                    actions['leading_zeros'] = st.checkbox(
                        "Leading 0s",
                        value=saved_actions.get('leading_zeros', True),
                        key=f"strip_lead_{selected_file}_{col_name}",
                        help="Remove leading zeros"
                    )
                
                # Note field - auto-saves when user presses Enter or clicks away
                saved_note = saved_actions.get('note', '')
                
                col_note, col_icon = st.columns([10, 1])
                with col_note:
                    new_note = st.text_input(
                        "Note",
                        value=saved_note,
                        key=f"numeric_note_{selected_file}_{col_name}",
                        placeholder="Press Enter to save..."
                    )
                with col_icon:
                    if new_note == saved_note:
                        st.markdown("✅")
                    else:
                        st.markdown("⚠️")
                
                actions['note'] = new_note
            
            elif selected_type == 'CODE':
                st.markdown("**Strip Actions:**")
                
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    actions['nonnumeric'] = st.checkbox(
                        "Non-numeric",
                        value=saved_actions.get('nonnumeric', True),
                        key=f"code_strip_nn_{selected_file}_{col_name}",
                        help="Remove $, commas, %, etc."
                    )
                with col_a2:
                    actions['decimal'] = st.checkbox(
                        "Decimal",
                        value=saved_actions.get('decimal', True),
                        key=f"code_strip_dec_{selected_file}_{col_name}",
                        help="Remove .00"
                    )
                
                # Note field
                saved_note = saved_actions.get('note', '')
                
                col_note, col_icon = st.columns([10, 1])
                with col_note:
                    new_note = st.text_input(
                        "Note",
                        value=saved_note,
                        key=f"code_note_{selected_file}_{col_name}",
                        placeholder="Press Enter to save..."
                    )
                with col_icon:
                    if new_note == saved_note:
                        st.markdown("✅")
                    else:
                        st.markdown("⚠️")
                
                actions['note'] = new_note
            
            elif selected_type == 'BOOLEAN':
                st.markdown("**Boolean Mapping:**")
                
                # Detect unique values
                unique_vals = list(set(col_samples))[:2]  # Take first 2 unique
                
                if len(unique_vals) >= 2:
                    
                    # Default mapping
                    default_true = saved_actions.get('true_value', unique_vals[0])
                    default_false = saved_actions.get('false_value', unique_vals[1])
                    
                    # Initialize session state for swapping
                    if f"bool_swap_{selected_file}_{col_name}" not in st.session_state:
                        st.session_state[f"bool_swap_{selected_file}_{col_name}"] = {
                            'true': default_true,
                            'false': default_false
                        }
                    
                    swap_state = st.session_state[f"bool_swap_{selected_file}_{col_name}"]
                    
                    col_b1, col_b2, col_b3 = st.columns([2, 1, 2])
                    with col_b1:
                        st.text_input(
                            "Maps to 1 (TRUE)",
                            value=swap_state['true'],
                            disabled=True,
                            key=f"bool_true_display_{selected_file}_{col_name}_{swap_state['true']}"
                        )
                    with col_b2:
                        if st.button("⇄", key=f"bool_swap_btn_{selected_file}_{col_name}", help="Swap mapping"):
                            # Swap the values
                            swap_state['true'], swap_state['false'] = swap_state['false'], swap_state['true']
                            st.rerun()
                    with col_b3:
                        st.text_input(
                            "Maps to 0 (FALSE)",
                            value=swap_state['false'],
                            disabled=True,
                            key=f"bool_false_display_{selected_file}_{col_name}_{swap_state['false']}"
                        )
                    
                    # Auto-generate mapping note
                    auto_note = f"1={swap_state['true']}, 0={swap_state['false']}"
                    actions['true_value'] = swap_state['true']
                    actions['false_value'] = swap_state['false']
                    
                    # Always use auto-generated note for boolean
                    actions['note'] = auto_note
                    
                    # Display note (read-only, shows current mapping)
                    st.text_input(
                        "Note (auto-generated)",
                        value=auto_note,
                        key=f"bool_note_{selected_file}_{col_name}_{swap_state['true']}",
                        disabled=True
                    )
                else:
                    st.warning("Need at least 2 unique values for boolean mapping")
            
            elif selected_type == 'DATE':
                st.markdown("**Date Format:**")
                
                # Auto-detect format
                detected_name, detected_fmt, unparseable_count = detect_date_format(col_samples)
                unparseable_pct = (unparseable_count / len(col_samples) * 100) if len(col_samples) > 0 else 0
                
                # Show detected format
                st.text(f"Detected input: {detected_name}")
                
                # Color code unparseable
                if unparseable_pct > 20:
                    unparse_color = "#ff0000"
                elif unparseable_pct > 5:
                    unparse_color = "#ff9900"
                else:
                    unparse_color = "#00cc00"
                
                st.markdown(f"<span style='color: {unparse_color};'>Unparseable: {unparseable_count:,} ({unparseable_pct:.1f}%)</span>", unsafe_allow_html=True)
                
                # Input format override
                input_format_options = ['Auto-detect', 'YYYY-MM-DD', 'MM/DD/YYYY', 'DD/MM/YYYY', 'Month DD, YYYY', 'Custom']
                current_input = saved_actions.get('input_format', 'Auto-detect')
                
                selected_input = st.selectbox(
                    "Input format override",
                    input_format_options,
                    index=input_format_options.index(current_input) if current_input in input_format_options else 0,
                    key=f"date_input_{selected_file}_{col_name}"
                )
                
                actions['input_format'] = selected_input
                
                # Custom input format
                if selected_input == 'Custom':
                    custom_input = st.text_input(
                        "Custom input format",
                        value=saved_actions.get('custom_input', ''),
                        key=f"date_custom_input_{selected_file}_{col_name}",
                        help="Use Python strftime format codes (e.g., %d/%m/%y)"
                    )
                    actions['custom_input'] = custom_input
                
                # Output format selection
                output_format_options = ['DD/MM/YYYY', 'YYYY-MM-DD', 'MM/DD/YYYY', 'Keep original']
                current_output = saved_actions.get('output_format', 'DD/MM/YYYY')
                
                selected_output = st.selectbox(
                    "Convert to format",
                    output_format_options,
                    index=output_format_options.index(current_output) if current_output in output_format_options else 0,
                    key=f"date_output_{selected_file}_{col_name}",
                    help="Output format for cleaned data"
                )
                
                actions['output_format'] = selected_output
                
                # Preview conversion
                if len(col_samples) > 0 and selected_output != 'Keep original':
                    # Pick a random sample
                    sample_val = random.choice(col_samples[:min(50, len(col_samples))])
                    
                    # Try to parse and convert
                    try:
                        # Determine input format
                        if selected_input == 'Auto-detect':
                            parse_fmt = detected_fmt
                        elif selected_input == 'Custom':
                            parse_fmt = actions.get('custom_input', detected_fmt)
                        else:
                            # Map display name to format code
                            format_map = {
                                'YYYY-MM-DD': '%Y-%m-%d',
                                'MM/DD/YYYY': '%m/%d/%Y',
                                'DD/MM/YYYY': '%d/%m/%Y',
                                'Month DD, YYYY': '%B %d, %Y'
                            }
                            parse_fmt = format_map.get(selected_input, detected_fmt)
                        
                        # Parse the date
                        parsed_date = datetime.strptime(str(sample_val).strip(), parse_fmt)
                        
                        # Convert to output format
                        output_map = {
                            'DD/MM/YYYY': '%d/%m/%Y',
                            'YYYY-MM-DD': '%Y-%m-%d',
                            'MM/DD/YYYY': '%m/%d/%Y'
                        }
                        output_fmt = output_map.get(selected_output, '%d/%m/%Y')
                        converted_val = parsed_date.strftime(output_fmt)
                        
                        st.success(f"Preview: `{sample_val}` → `{converted_val}`")
                    except:
                        st.warning(f"Preview: `{sample_val}` → Could not parse")
            
            elif selected_type == 'TEXT':
                st.markdown("**Text Column:**")
                saved_note = saved_actions.get('note', '')
                
                col_note, col_icon = st.columns([10, 1])
                with col_note:
                    new_note = st.text_input(
                        "Note",
                        value=saved_note,
                        key=f"text_note_{selected_file}_{col_name}",
                        placeholder="Press Enter to save..."
                    )
                with col_icon:
                    if new_note == saved_note:
                        st.markdown("✅")
                    else:
                        st.markdown("⚠️")
                
                actions['note'] = new_note
            
            elif selected_type == 'IGNORE':
                st.markdown("**Ignored Column:**")
                saved_note = saved_actions.get('note', '')
                
                col_note, col_icon = st.columns([10, 1])
                with col_note:
                    new_note = st.text_input(
                        "Reason for ignoring",
                        value=saved_note,
                        key=f"ignore_note_{selected_file}_{col_name}",
                        placeholder="Press Enter to save..."
                    )
                with col_icon:
                    if new_note == saved_note:
                        st.markdown("✅")
                    else:
                        st.markdown("⚠️")
                
                actions['note'] = new_note
            
            # Auto-save on change (only save actions if type matches)
            needs_save = False
            save_actions = None
            
            if selected_type != current_type:
                needs_save = True
                if selected_type in ['NUMERIC', 'CODE', 'BOOLEAN', 'DATE', 'TEXT', 'IGNORE']:
                    save_actions = actions
            elif actions != current_schema.get('actions', {}):
                # Actions changed (including note changes)
                needs_save = True
                save_actions = actions
            
            if needs_save:
                save_column_type(selected_file, col_name, selected_type, save_actions)
        
        with col_right:
            st.markdown("**Sample Values:**")
            
            if len(display_samples) == 0:
                st.warning("No valid samples found")
            else:
                # Display in rows of 6
                for i in range(0, len(display_samples), 6):
                    batch = display_samples[i:i+6]
                    sample_text = "   ".join([f"`{v}`" for v in batch])
                    st.caption(sample_text)
            
            # Unique values in expander
            unique_vals = list(set(col_samples))[:60]
            with st.expander(f"🔍 Unique Values ({len(unique_vals)} shown)"):
                if len(unique_vals) == 0:
                    st.caption("No unique values")
                else:
                    # Display in rows of 6
                    for i in range(0, len(unique_vals), 6):
                        batch = unique_vals[i:i+6]
                        unique_text = "   ".join([f"`{v}`" for v in batch])
                        st.caption(unique_text)
    


if __name__ == "__main__":
    main()