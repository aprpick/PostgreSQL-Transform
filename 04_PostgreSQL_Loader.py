import psycopg2
import os
import sys
from pathlib import Path
from datetime import datetime

# Fix emoji/unicode output on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).parent

# INPUTS
CLEANED_DATA = PROJECT_ROOT / "02.1_Cleaned_Data"       # From Script 02
DDL_FILE = PROJECT_ROOT / "03.1_PostgreSQL_DDL.sql"     # From Script 03

# PostgreSQL connection settings
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'assessor_data',
    'user': 'postgres',
    'password': ''  # Leave blank if using trust auth
}

# Tables to load (in order) - maps CSV filename to table name
TABLE_MAP = {
    'Cleaned_01_Assessor_-_Parcel_Sales_2023_2025.csv': 'assessor_parcel_sales_2023_2025',
    'Cleaned_02_Assessor_-_Parcel_Addresses_20260205.csv': 'assessor_parcel_addresses_20260205',
    'Cleaned_03_Assessor_-_Assessed_Values_2023_2025.csv': 'assessor_assessed_values_2023_2025',
    'Cleaned_04_Assessor_-_Single_and_Multi-Family_Improvement_Characteristics_20260205_websiteDL.csv': 'assessor_single_and_multi_family_improvement_characteristics_20'
}

# Tables that have DATE columns in DD/MM/YYYY format
DATE_TABLES = ['assessor_parcel_sales_2023_2025']


def connect():
    """Connect to PostgreSQL"""
    print("🔌 Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    print(f"  ✅ Connected to '{DB_CONFIG['database']}' on {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    return conn


def drop_tables(conn):
    """Drop all tables if they exist"""
    print("\n🗑️  Dropping existing tables...")
    cur = conn.cursor()
    for table_name in TABLE_MAP.values():
        cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        print(f"  Dropped: {table_name}")
    conn.commit()
    cur.close()
    print("  ✅ All tables dropped")


def run_ddl(conn):
    """Run DDL to create tables"""
    print(f"\n🏗️  Creating tables from DDL...")
    
    with open(DDL_FILE, 'r', encoding='utf-8') as f:
        ddl = f.read()
    
    cur = conn.cursor()
    cur.execute(ddl)
    conn.commit()
    cur.close()
    print(f"  ✅ Tables created from {DDL_FILE.name}")


def load_table(conn, csv_file, table_name):
    """Load a CSV file into a PostgreSQL table"""
    print(f"\n📥 Loading: {csv_file.name}")
    print(f"  → Table: {table_name}")
    
    cur = conn.cursor()
    
    # Set datestyle for tables with DD/MM/YYYY dates
    if table_name in DATE_TABLES:
        cur.execute("SET datestyle = 'DMY';")
        print(f"  📅 DateStyle set to DMY")
    
    # Use COPY command with absolute path
    abs_path = str(csv_file.absolute()).replace('\\', '/')
    
    start_time = datetime.now()
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        cur.copy_expert(
            f"COPY {table_name} FROM STDIN CSV HEADER",
            f
        )
    
    conn.commit()
    
    elapsed = (datetime.now() - start_time).seconds
    
    # Get row count
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cur.fetchone()[0]
    
    cur.close()
    print(f"  ✅ Loaded {count:,} rows in {elapsed}s")
    return count


def verify_all(conn):
    """Verify row counts for all tables"""
    print("\n📊 Verifying row counts...")
    cur = conn.cursor()
    
    total = 0
    print(f"\n{'Table':<65} {'Rows':>12}")
    print("-" * 80)
    
    for table_name in TABLE_MAP.values():
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]
        total += count
        print(f"{table_name:<65} {count:>12,}")
    
    print("-" * 80)
    print(f"{'TOTAL':<65} {total:>12,}")
    
    cur.close()
    return total


def main():
    print("=" * 60)
    print("📦 PHASE 4: PostgreSQL Data Loader")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check cleaned data exists
    csv_files = {
        name: CLEANED_DATA / name 
        for name in TABLE_MAP.keys()
    }
    
    print("\n📁 Checking cleaned CSV files...")
    all_exist = True
    for name, path in csv_files.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {name} ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ MISSING: {name}")
            all_exist = False
    
    if not all_exist:
        print("\n❌ Some files are missing! Run Script 02 first.")
        return
    
    # Connect to PostgreSQL
    try:
        conn = connect()
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("Check your DB_CONFIG settings at the top of this script.")
        return
    
    try:
        # Drop existing tables
        drop_tables(conn)
        
        # Create tables from DDL
        run_ddl(conn)
        
        # Load each CSV
        print("\n" + "=" * 60)
        print("📥 LOADING DATA")
        print("=" * 60)
        
        total_rows = 0
        start_time = datetime.now()
        
        for csv_name, table_name in TABLE_MAP.items():
            csv_file = csv_files[csv_name]
            rows = load_table(conn, csv_file, table_name)
            total_rows += rows
        
        # Verify
        verify_all(conn)
        
        elapsed = (datetime.now() - start_time).seconds
        
        print(f"\n{'=' * 60}")
        print(f"✅ LOAD COMPLETE")
        print(f"{'=' * 60}")
        print(f"Total rows loaded: {total_rows:,}")
        print(f"Total time: {elapsed}s")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
        print("🔌 Connection closed")


if __name__ == "__main__":
    main()