# Install the following Package
# pip install pyyaml

import yaml
import mysql.connector

# ==============================================================================
# 1. DATABASE CONFIGURATION
# ==============================================================================
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root', 
    'database': 'map_project'
}

# ==============================================================================
# 2. CONFIGURABLE DISCOUNT RATES (LPP MATRIX)
# ==============================================================================
# Rates taken from 'LPP Calculation.xlsx'.
# You can easily adjust percentages here or add new brands/subcategories.
LPP_DISCOUNT_RATES = {
    'HP': {
        'Laptop':   0.034,
        'Monitor':  0.012,
        'Toner':    0.091,
        'Laserjet': 0.065,
        'Inkjet':   0.012,
        'Desktop':  0.091,
        'Ink':      0.065
    },
    'DELL': {
        'Laptop':   0.078,
        'Monitor':  0.056,
        'Toner':    0.023,
        'Laserjet': 0.035,
        'Inkjet':   0.056,
        'Desktop':  0.023,
        'Ink':      0.035
    }
}

# Mapping short codes found in PL strings to standardized subcategories
SUBCAT_CODE_MAP = {
    'Laptop':  'Laptop',
    'Monitor': 'Monitor',
    'Desktop': 'Desktop',
    'TON':     'Toner',
    'LJ':      'Laserjet',
    'IJ':      'Inkjet',
    'INK':     'Ink'
}

# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================
def extract_brand_and_subcategory(pl_string):
    """
    Parses PL string to detect Brand and standard Subcategory.
    Examples:
        'DELL0X_PC_Laptop' -> Brand: 'DELL', Subcategory: 'Laptop'
        'HP4Z_PH_LJ'       -> Brand: 'HP',   Subcategory: 'Laserjet'
    """
    if not pl_string:
        return 'UNKNOWN', 'UNKNOWN'
    
    # 1. Detect Brand
    pl_upper = pl_string.upper()
    if pl_upper.startswith('DELL'):
        brand = 'DELL'
    elif pl_upper.startswith('HP'):
        brand = 'HP'
    else:
        brand = 'OTHER'

    # 2. Extract Subcategory
    parts = pl_string.split('_')
    raw_subcat = parts[-1] if len(parts) >= 3 else parts[-1]
    standard_subcat = SUBCAT_CODE_MAP.get(raw_subcat, raw_subcat)

    return brand, standard_subcat

def calculate_lpp(map_price, brand, subcategory):
    """
    Formula:
        Discount_Amount = MAP * Discount_Rate
        LPP = MAP - Discount_Amount  (i.e., MAP * (1 - Discount_Rate))
    """
    if map_price is None:
        return None

    # Get rate from config matrix; defaults to 0.0 if not defined
    brand_rates = LPP_DISCOUNT_RATES.get(brand, {})
    discount_rate = brand_rates.get(subcategory, 0.0)

    # Calculate LPP rounded to 2 decimal places
    lpp = float(map_price) * (1.0 - discount_rate)
    return round(lpp, 2)

# ==============================================================================
# 4. MAIN INGESTION WORKFLOW
# ==============================================================================
def main():
    yaml_path = r'D:\Github\MAP\Week 2\Resources\MAP, PL, SKU .yaml'

    print(f"Loading YAML file: {yaml_path}")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        # Using SafeLoader to read the list of product dictionaries
        items = yaml.safe_load(f)

    print(f"Loaded {len(items)} records from YAML. Processing calculations...")

    records_to_insert = []
    for item in items:
        sku = item.get('sku')
        pl = item.get('PL')
        map_price = item.get('MAP')

        brand, subcat = extract_brand_and_subcategory(pl)
        lpp = calculate_lpp(map_price, brand, subcat)

        records_to_insert.append((sku, pl, map_price, lpp))

    print(f"Ready to insert {len(records_to_insert)} rows into `price_list`.")

    # Connecting to MySQL
    print("Connecting to MySQL...")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    insert_query = """
        INSERT IGNORE INTO price_list (SKU, PL, MAP, LPP)
        VALUES (%s, %s, %s, %s)
    """

    print("Inserting data into database...")
    cursor.executemany(insert_query, records_to_insert)
    conn.commit()

    print(f"Done! {cursor.rowcount} rows inserted into `price_list` successfully.")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()

