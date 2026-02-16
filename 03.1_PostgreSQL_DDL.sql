-- Table: assessor_parcel_sales_2023_2025
-- Source: 01_Assessor_-_Parcel_Sales_2023_2025.csv
CREATE TABLE assessor_parcel_sales_2023_2025 (
    pin VARCHAR(20) NOT NULL,
    year SMALLINT NOT NULL,
    township_code VARCHAR(5) NOT NULL,
    neighborhood_code VARCHAR(10) NOT NULL,
    class VARCHAR(5) NOT NULL,
    sale_date DATE NOT NULL,
    sale_price INTEGER NOT NULL,
    sale_document_num VARCHAR(15) NOT NULL,
    sale_deed_type TEXT NOT NULL,
    mydec_deed_type TEXT NULL,
    sale_seller_name TEXT NULL,
    is_multisale BOOLEAN NOT NULL,
    num_parcels_sale SMALLINT NOT NULL,
    sale_buyer_name TEXT NULL,
    sale_filter_same_sale_within_365 BOOLEAN NOT NULL,
    sale_filter_less_than_10k BOOLEAN NOT NULL,
    sale_filter_deed_type BOOLEAN NOT NULL,
    row_id VARCHAR(10) NOT NULL
);

COMMENT ON COLUMN assessor_parcel_sales_2023_2025.pin IS 'Parcel Identification Number (PIN)';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.year IS 'Year';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.township_code IS 'Township code';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.neighborhood_code IS 'Assessor neighborhood code, first two digits are township, last three are neighborhood';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.class IS 'Property class';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.sale_date IS 'Sale date (recorded, not executed)';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.sale_price IS 'Sale price';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.sale_document_num IS 'Sale document number. Corresponds to Clerk''s document number';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.sale_deed_type IS 'Sale deed type';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.mydec_deed_type IS 'Deed type from MyDec, more granular than CCAO deed type';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.sale_seller_name IS 'Sale seller name';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.is_multisale IS 'Indicates whether a parcel was sold individually or as part of a larger group of PINs  (1=False, 0=True)';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.num_parcels_sale IS 'The number of parcels that were part of the sale';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.sale_buyer_name IS 'Sale buyer name';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.sale_filter_same_sale_within_365 IS 'Remove sale with the same value (for the same PIN) within 365 days  (1=False, 0=True)';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.sale_filter_less_than_10k IS 'Indicator for whether sale is less than $10K FMW  (1=False, 0=True)';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.sale_filter_deed_type IS 'Indicator for quit claim, executor, beneficiary and missing deed types  (1=False, 0=True)';
COMMENT ON COLUMN assessor_parcel_sales_2023_2025.row_id IS 'Unique row key for API';

-- Table: assessor_parcel_addresses_20260205
-- Source: 02_Assessor_-_Parcel_Addresses_20260205.csv
CREATE TABLE assessor_parcel_addresses_20260205 (
    pin VARCHAR(20) NOT NULL,
    pin10 VARCHAR(15) NOT NULL,
    tax_year SMALLINT NOT NULL,
    property_address TEXT NULL,
    property_city TEXT NULL,
    property_zip VARCHAR(10) NULL,
    mailing_name TEXT NULL,
    mailing_address TEXT NULL,
    mailing_city TEXT NULL,
    mailing_state VARCHAR(5) NULL,
    mailing_zip VARCHAR(10) NULL,
    row_id VARCHAR(25) NOT NULL
);

COMMENT ON COLUMN assessor_parcel_addresses_20260205.pin IS 'Parcel Identification Number (PIN)';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.pin10 IS 'Parcel Identification Number (10-digit)';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.tax_year IS 'Tax year';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.property_address IS 'Property street address';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.property_city IS 'Property city';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.property_zip IS 'Property zip code';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.mailing_name IS 'Taxpayer mailing name';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.mailing_address IS 'Taxpayer mailing street address';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.mailing_city IS 'Taxpayer mailing city';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.mailing_state IS 'Taxpayer mailing state';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.mailing_zip IS 'Taxpayer mailing zip code';
COMMENT ON COLUMN assessor_parcel_addresses_20260205.row_id IS 'Unique row key for API';

-- Table: assessor_assessed_values_2023_2025
-- Source: 03_Assessor_-_Assessed_Values_2023_2025.csv
CREATE TABLE assessor_assessed_values_2023_2025 (
    pin VARCHAR(20) NOT NULL,
    tax_year SMALLINT NOT NULL,
    class VARCHAR(5) NOT NULL,
    township_code VARCHAR(5) NOT NULL,
    township_name TEXT NOT NULL,
    neighborhood_code VARCHAR(10) NOT NULL,
    mailed_bldg INTEGER NOT NULL,
    mailed_land INTEGER NOT NULL,
    mailed_tot INTEGER NOT NULL,
    mailed_hie INTEGER NOT NULL,
    certified_bldg INTEGER NULL,
    certified_land INTEGER NULL,
    certified_tot INTEGER NULL,
    certified_hie INTEGER NULL,
    board_bldg INTEGER NULL,
    board_land INTEGER NULL,
    board_tot INTEGER NULL,
    board_hie SMALLINT NULL,
    row_id VARCHAR(25) NOT NULL
);

-- Table: assessor_single_and_multi_family_improvement_characteristics_20260205_websitedl
-- Source: 04_Assessor_-_Single_and_Multi-Family_Improvement_Characteristics_20260205_websiteDL.csv
CREATE TABLE assessor_single_and_multi_family_improvement_characteristics_20260205_websitedl (
    pin VARCHAR(20) NOT NULL,
    tax_year SMALLINT NOT NULL,
    card_num VARCHAR(5) NOT NULL,
    class VARCHAR(5) NOT NULL,
    township_code VARCHAR(5) NOT NULL,
    proration_key_pin VARCHAR(20) NULL,
    pin_proration_rate NUMERIC(6,3) NOT NULL,
    card_proration_rate NUMERIC(17,3) NULL,
    cdu VARCHAR(5) NULL,
    pin_is_multicard BOOLEAN NOT NULL,
    pin_num_cards SMALLINT NOT NULL,
    pin_is_multiland BOOLEAN NOT NULL,
    pin_num_landlines SMALLINT NOT NULL,
    year_built SMALLINT NULL,
    building_sqft INTEGER NOT NULL,
    land_sqft INTEGER NULL,
    num_bedrooms SMALLINT NULL,
    num_rooms SMALLINT NULL,
    num_full_baths SMALLINT NULL,
    num_half_baths SMALLINT NULL,
    num_fireplaces SMALLINT NULL,
    type_of_residence VARCHAR(15) NULL,
    construction_quality VARCHAR(10) NULL,
    num_apartments VARCHAR(10) NULL,
    attic_finish VARCHAR(15) NULL,
    garage_attached BOOLEAN NULL,
    garage_area_included BOOLEAN NULL,
    garage_size NUMERIC(4,1) NULL,
    garage_ext_wall_material TEXT NULL,
    attic_type BOOLEAN NULL,
    basement_type VARCHAR(10) NULL,
    ext_wall_material TEXT NULL,
    central_heating VARCHAR(20) NULL,
    repair_condition VARCHAR(20) NULL,
    basement_finish VARCHAR(20) NULL,
    roof_material TEXT NULL,
    single_v_multi_family BOOLEAN NULL,
    site_desirability VARCHAR(30) NULL,
    num_commercial_units SMALLINT NULL,
    porch VARCHAR(20) NULL,
    central_air BOOLEAN NULL,
    design_plan BOOLEAN NULL,
    row_id VARCHAR(25) NOT NULL
);
