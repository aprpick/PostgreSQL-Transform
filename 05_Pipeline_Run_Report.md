# Pipeline Run Report

**Generated:** 2026-02-17 09:37:06
**Status:** ✅ SUCCESS
**Total Time:** 1632s

## Summary

| Script | Status | Time | Notes |
|--------|--------|------|-------|
| 02_Data_Precleaning.py | ✅ Success | 1341s | Loaded 216,550 rows |
| 03_PostgreSQL_schema_generator.py | ✅ Success | 150s | Loaded 216,550 rows |
| 04_PostgreSQL_Loader.py | ✅ Success | 140s | ✅ Loaded 216,550 rows in 1s |

## Detailed Results

### ✅ 02_Data_Precleaning.py

- **Status:** Success
- **Start Time:** 09:09:54
- **Duration:** 1341s

**Output:**
```
============================================================
01.5 - DATA PRECLEANING
============================================================

📄 Processing: 01_Assessor_-_Parcel_Sales_2023_2025.csv
  Loaded 216,550 rows
  🔧 Cleaning: pin (CODE)
  🔧 Cleaning: year (NUMERIC)
  🔧 Cleaning: township_code (CODE)
  🔧 Cleaning: neighborhood_code (CODE)
  🔧 Cleaning: class (CODE)
  🔧 Cleaning: sale_date (DATE)
  🚫 Dropping: is_mydec_date (IGNORE)
  🔧 Cleaning: sale_price (NUMERIC)
  🔧 Cleaning: sale_document_num (CODE)
  🔧 Cleaning: sale_deed_type (TEXT)
  🔧 Cleaning: mydec_deed_type (TEXT)
  🔧 Cleaning: sale_seller_name (TEXT)
  🔧 Cleaning: is_multisale (BOOLEAN)
  🔧 Cleaning: num_parcels_sale (NUMERIC)
  🔧 Cleaning: sale_buyer_name (TEXT)
  🚫 Dropping: sale_type (IGNORE)
  🔧 Cleaning: sale_filter_same_sale_within_365 (BOOLEAN)
  🔧 Cleaning: sale_filter_less_than_10k (BOOLEAN)
  🔧 Cleaning: sale_filter_deed_type (BOOLEAN)
... (70 lines omitted) ...
  🔧 Cleaning: garage_attached (BOOLEAN)
  🔧 Cleaning: garage_area_included (BOOLEAN)
  🔧 Cleaning: garage_size (NUMERIC)
  🔧 Cleaning: garage_ext_wall_material (TEXT)
  🔧 Cleaning: attic_type (BOOLEAN)
  🔧 Cleaning: basement_type (TEXT)
  🔧 Cleaning: ext_wall_material (TEXT)
  🔧 Cleaning: central_heating (TEXT)
  🔧 Cleaning: repair_condition (TEXT)
  🔧 Cleaning: basement_finish (TEXT)
  🔧 Cleaning: roof_material (TEXT)
  🔧 Cleaning: single_v_multi_family (BOOLEAN)
  🔧 Cleaning: site_desirability (TEXT)
  🔧 Cleaning: num_commercial_units (NUMERIC)
  🚫 Dropping: renovation (IGNORE)
  🔧 Cleaning: porch (TEXT)
  🔧 Cleaning: central_air (BOOLEAN)
  🔧 Cleaning: design_plan (BOOLEAN)
  🔧 Cleaning: row_id (CODE)
  ✅ Saved: c:\Documents-C\PostgresSQL_Transform\02.1_Cleaned_Data\Cleaned_04_Assessor_-_Single_and_Multi-Family_Improvement_Characteristics_20260205_websiteDL.csv (3,306,906 rows)

📊 Report saved: c:\Documents-C\PostgresSQL_Transform\02.1_Cleaning_Report.md
============================================================
✅ PRECLEANING COMPLETE
============================================================
```

---

### ✅ 03_PostgreSQL_schema_generator.py

- **Status:** Success
- **Start Time:** 09:32:15
- **Duration:** 150s

**Output:**
```
======================================================================
PHASE 3: POSTGRESQL SCHEMA GENERATOR
======================================================================

📊 Analyzing: 01_Assessor_-_Parcel_Sales_2023_2025.csv
  Loaded 216,550 rows
  Table name: assessor_parcel_sales_2023_2025
  🔍 pin (CODE)
  🔍 year (NUMERIC)
  🔍 township_code (CODE)
  🔍 neighborhood_code (CODE)
  🔍 class (CODE)
  🔍 sale_date (DATE)
  🔍 sale_price (NUMERIC)
  🔍 sale_document_num (CODE)
  🔍 sale_deed_type (TEXT)
  🔍 mydec_deed_type (TEXT)
  🔍 sale_seller_name (TEXT)
  🔍 is_multisale (BOOLEAN)
  🔍 num_parcels_sale (NUMERIC)
  🔍 sale_buyer_name (TEXT)
  🔍 sale_filter_same_sale_within_365 (BOOLEAN)
  🔍 sale_filter_less_than_10k (BOOLEAN)
  🔍 sale_filter_deed_type (BOOLEAN)
  🔍 row_id (CODE)
... (72 lines omitted) ...
  🔍 garage_area_included (BOOLEAN)
  🔍 garage_size (NUMERIC)
  🔍 garage_ext_wall_material (TEXT)
  🔍 attic_type (BOOLEAN)
  🔍 basement_type (TEXT)
  🔍 ext_wall_material (TEXT)
  🔍 central_heating (TEXT)
  🔍 repair_condition (TEXT)
  🔍 basement_finish (TEXT)
  🔍 roof_material (TEXT)
  🔍 single_v_multi_family (BOOLEAN)
  🔍 site_desirability (TEXT)
  🔍 num_commercial_units (NUMERIC)
  🔍 porch (TEXT)
  🔍 central_air (BOOLEAN)
  🔍 design_plan (BOOLEAN)
  🔍 row_id (CODE)
  ✅ Analysis complete

💾 Saved schema: c:\Documents-C\PostgresSQL_Transform\03.1_PostgreSQL_Schema.json
💾 Saved DDL: c:\Documents-C\PostgresSQL_Transform\03.1_PostgreSQL_DDL.sql
💾 Saved report: c:\Documents-C\PostgresSQL_Transform\03.1_Optimization_Report.md
======================================================================
✅ SCHEMA GENERATION COMPLETE
======================================================================
```

---

### ✅ 04_PostgreSQL_Loader.py

- **Status:** Success
- **Start Time:** 09:34:46
- **Duration:** 140s

**Output:**
```
============================================================
📦 PHASE 4: PostgreSQL Data Loader
============================================================
Generated: 2026-02-17 09:34:46

📁 Checking cleaned CSV files...
  ✅ Cleaned_01_Assessor_-_Parcel_Sales_2023_2025.csv (31.7 MB)
  ✅ Cleaned_02_Assessor_-_Parcel_Addresses_20260205.csv (729.4 MB)
  ✅ Cleaned_03_Assessor_-_Assessed_Values_2023_2025.csv (591.3 MB)
  ✅ Cleaned_04_Assessor_-_Single_and_Multi-Family_Improvement_Characteristics_20260205_websiteDL.csv (737.9 MB)
🔌 Connecting to PostgreSQL...
  ✅ Connected to 'assessor_data' on localhost:5432

🗑️  Dropping existing tables...
  Dropped: assessor_parcel_sales_2023_2025
  Dropped: assessor_parcel_addresses_20260205
  Dropped: assessor_assessed_values_2023_2025
  Dropped: assessor_single_and_multi_family_improvement_characteristics_20
  ✅ All tables dropped

🏗️  Creating tables from DDL...
  ✅ Tables created from 03.1_PostgreSQL_DDL.sql

============================================================
📥 LOADING DATA
... (11 lines omitted) ...
📥 Loading: Cleaned_03_Assessor_-_Assessed_Values_2023_2025.csv
  → Table: assessor_assessed_values_2023_2025
  ✅ Loaded 5,592,069 rows in 21s

📥 Loading: Cleaned_04_Assessor_-_Single_and_Multi-Family_Improvement_Characteristics_20260205_websiteDL.csv
  → Table: assessor_single_and_multi_family_improvement_characteristics_20
  ✅ Loaded 3,306,906 rows in 36s

📊 Verifying row counts...

Table                                                                     Rows
--------------------------------------------------------------------------------
assessor_parcel_sales_2023_2025                                        216,550
assessor_parcel_addresses_20260205                                   5,592,069
assessor_assessed_values_2023_2025                                   5,592,069
assessor_single_and_multi_family_improvement_characteristics_20      3,306,906
--------------------------------------------------------------------------------
TOTAL                                                               14,707,594

============================================================
✅ LOAD COMPLETE
============================================================
Total rows loaded: 14,707,594
Total time: 139s
🔌 Connection closed
```

---

## Issues Found

✅ No issues found - pipeline ran cleanly!
