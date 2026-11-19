import openpyxl
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
# 2. Q4 PROMOTION OFFER MAPPING
# ==============================================================================
# Offers defined for Q4 (Aug - Oct) in 'Promotion SKU.xlsx' by Category
Q4_OFFERS = {
    'Supply': '20% off ink',
    'Print Hardware': '$10 off laser jet',
    'PC': '15% off'
}

# ==============================================================================
# 3. MAIN WORKFLOW
# ==============================================================================
def main():
    excel_path = r'D:\Github\MAP\Week 2\Resources\Promotion SKU.xlsx'

    # Step 1: Read the promotional SKUs from Excel (Column B, rows 16 to 115)
    print(f"Reading Promotional SKUs from: {excel_path}...")
    wb = openpyxl.load_workbook(excel_path, read_only=True)
    sheet = wb.active

    promo_skus = set()
    for row in sheet.iter_rows(min_row=16, max_row=115, min_col=2, max_col=2, values_only=True):
        val = row[0]
        if val is not None:
            sku_clean = str(val).strip()
            if sku_clean:
                promo_skus.add(sku_clean)

    wb.close()
    print(f"Loaded {len(promo_skus)} promotional SKUs from Excel.")

    # Step 2: Query DB to find PL and Category for these SKUs
    print("Connecting to MySQL...")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    print("Fetching PL and Category details from `category_mapping`...")
    cursor.execute("SELECT SKU, PL, Category FROM category_mapping")
    all_cat_rows = cursor.fetchall()

    # Build a lookup dictionary: SKU -> (PL, Category)
    sku_lookup = {row[0]: (row[1], row[2]) for row in all_cat_rows}

    # Step 3: Match promotional SKUs with their Q4 offer
    records_to_insert = []
    season = "Q4"

    for sku in promo_skus:
        if sku in sku_lookup:
            pl, category = sku_lookup[sku]
            offer = Q4_OFFERS.get(category, "Promotional Offer")
            records_to_insert.append((sku, pl, season, offer))
        else:
            print(f"Notice: Promotional SKU '{sku}' not found in `category_mapping`, skipping.")

    print(f"Ready to insert {len(records_to_insert)} rows for Season '{season}'.")

    # Step 4: Insert records into promotion table
    insert_query = """
        INSERT IGNORE INTO promotion (SKU, PL, Season, Promotion)
        VALUES (%s, %s, %s, %s)
    """

    print("Inserting data into `promotion` table...")
    cursor.executemany(insert_query, records_to_insert)
    conn.commit()

    print(f"Done! {cursor.rowcount} rows inserted successfully.")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()

