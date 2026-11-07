# Install the following Package
# pip install mysql-connector-python

import json
import mysql.connector

# Database connection configuration
# Update 'YOUR_ROOT_PASSWORD' with your actual MySQL root password
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'map_project'
}

# Mapping abbreviations in PL to readable Subcategory names
SUBCAT_MAP = {
    'Laptop': 'Laptop',
    'Monitor': 'Monitor',
    'Desktop': 'Desktop',
    'TON': 'Toner',
    'LJ': 'Laserjet',
    'IJ': 'Inkjet',
    'INK': 'Ink'
}

def derive_subcategory(pl_string):
    """
    Extracts and maps the subcategory from a PL string.
    Example:
        'DELL0X_PC_Laptop' -> splits to ['DELL0X', 'PC', 'Laptop'] -> 'Laptop'
        'DELLDF_SUP_TON'   -> splits to ['DELLDF', 'SUP', 'TON']   -> 'Toner'
    """
    if not pl_string:
        return None
    parts = pl_string.split('_')
    raw_subcat = parts[-1] if len(parts) >= 3 else parts[-1]
    return SUBCAT_MAP.get(raw_subcat, raw_subcat)

def main():
    json_path = r'D:\Github\MAP\Week 2\Resources\PL,SKU.json'

    print("Reading PL,SKU.json...")
    records_to_insert = []

    with open(json_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            sku = item.get('sku')
            pl = item.get('PL')
            subcat = derive_subcategory(pl)
            records_to_insert.append((sku, pl, subcat))

    print(f"Parsed {len(records_to_insert)} records.")

    print("Connecting to MySQL...")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    insert_query = """
        INSERT IGNORE INTO pl (SKU, PL, SUB_CATEGORY)
        VALUES (%s, %s, %s)
    """

    print("Inserting records into `pl` table...")
    cursor.executemany(insert_query, records_to_insert)
    conn.commit()

    print(f"Success! {cursor.rowcount} rows inserted.")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()

