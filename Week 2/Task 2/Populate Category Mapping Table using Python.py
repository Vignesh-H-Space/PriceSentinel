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
# 2. STANDARDIZED MAPPINGS
# ==============================================================================
# Category code -> Full descriptive name
CATEGORY_MAP = {
    'PC':  'PC',
    'SUP': 'Supply',
    'PH':  'Print Hardware'
}

# Subcategory short code -> Full descriptive name
SUBCAT_MAP = {
    'Laptop':  'Laptop',
    'Monitor': 'Monitor',
    'Desktop': 'Desktop',
    'TON':     'Toner',
    'LJ':      'Laserjet',
    'IJ':      'Inkjet',
    'INK':     'Ink'
}

def parse_category_and_subcategory(pl_string):
    """
    Parses PL string to extract category and subcategory.
    Examples:
        'DELL0X_PC_Laptop' -> splits to ['DELL0X', 'PC', 'Laptop']
                              Category: 'PC', Subcategory: 'Laptop'
        'DELLDF_SUP_TON'   -> splits to ['DELLDF', 'SUP', 'TON']
                              Category: 'Supply', Subcategory: 'Toner'
        'HP4Z_PH_LJ'       -> splits to ['HP4Z', 'PH', 'LJ']
                              Category: 'Print Hardware', Subcategory: 'Laserjet'
    """
    if not pl_string:
        return 'UNKNOWN', 'UNKNOWN'
    
    parts = pl_string.split('_')
    
    if len(parts) >= 3:
        raw_cat = parts[1]
        raw_subcat = parts[2]
    elif len(parts) == 2:
        raw_cat = parts[0]
        raw_subcat = parts[1]
    else:
        raw_cat = 'UNKNOWN'
        raw_subcat = parts[0]

    cat = CATEGORY_MAP.get(raw_cat, raw_cat)
    subcat = SUBCAT_MAP.get(raw_subcat, raw_subcat)

    return cat, subcat

# ==============================================================================
# 3. MAIN WORKFLOW
# ==============================================================================
def main():
    print("Connecting to MySQL...")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Step 1: Read existing PL data from the database
    print("Reading data from `pl` table...")
    cursor.execute("SELECT SKU, PL FROM pl")
    pl_rows = cursor.fetchall()
    print(f"Fetched {len(pl_rows)} rows from `pl`.")

    # Step 2: Transform and prepare records
    records_to_insert = []
    for sku, pl in pl_rows:
        category, subcategory = parse_category_and_subcategory(pl)
        records_to_insert.append((sku, pl, category, subcategory))

    # Step 3: Insert into category_mapping table
    insert_query = """
        INSERT IGNORE INTO category_mapping (SKU, PL, Category, sub_category)
        VALUES (%s, %s, %s, %s)
    """

    print("Inserting into `category_mapping` table...")
    cursor.executemany(insert_query, records_to_insert)
    conn.commit()

    print(f"Done! {cursor.rowcount} rows inserted successfully.")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()

