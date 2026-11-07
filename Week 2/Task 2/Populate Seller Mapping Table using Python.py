# Install the following Package
# pip install openpyxl

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
# 2. MAIN INGESTION WORKFLOW
# ==============================================================================
def main():
    excel_path = r'D:\Github\MAP\Week 2\Resources\Seller Details.xlsx'

    print(f"Opening Excel file: {excel_path}...")
    # read_only=True ensures fast loading and low memory usage
    wb = openpyxl.load_workbook(excel_path, read_only=True)
    sheet = wb.active

    records_to_insert = []
    
    # Read rows (skipping the header row 1)
    # Column A: Ssellers_name -> Seller_Name
    # Column B: homologated_sellers -> Homologated_Name
    for row in sheet.iter_rows(min_row=2, values_only=True):
        raw_seller = row[0]
        homologated_seller = row[1]

        # Ignore empty rows if any
        if raw_seller is not None and homologated_seller is not None:
            seller_name = str(raw_seller).strip()
            homo_name = str(homologated_seller).strip()
            records_to_insert.append((seller_name, homo_name))

    wb.close()
    print(f"Parsed {len(records_to_insert)} seller mapping records from Excel.")

    # Connecting to MySQL
    print("Connecting to MySQL...")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO seller_mapping (Seller_Name, Homologated_Name)
        VALUES (%s, %s)
    """

    print("Inserting data into `seller_mapping` table...")
    cursor.executemany(insert_query, records_to_insert)
    conn.commit()

    print(f"Done! {cursor.rowcount} rows inserted successfully.")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()

