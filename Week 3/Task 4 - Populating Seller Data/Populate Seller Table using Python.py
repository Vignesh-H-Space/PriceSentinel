import os
import glob
import csv
import time
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
# 2. PATHS & SETTINGS
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = r"D:\Github\MAP\Week 3\Resources\Seller Data"
BATCH_SIZE = 5000  # Number of rows inserted per SQL batch

def clean_str(val):
    """Strips whitespace and returns None if empty."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None

def clean_price(val):
    """Safely converts price strings to float, returns None if empty or invalid."""
    if val is None:
        return None
    try:
        s = str(val).replace("$", "").replace("₹", "").replace(",", "").strip()
        return float(s) if s else None
    except (ValueError, TypeError):
        return None

# ==============================================================================
# 3. MAIN INGESTION WORKFLOW
# ==============================================================================
def main():
    start_time = time.time()
    
    # 1. Find all daily CSV files
    csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
    if not csv_files:
        print(f"[Error] No CSV files found in: {DATA_DIR}")
        return

    print("=" * 70)
    print("  TASK 4: POPULATING SELLER TABLE FROM DAILY CSV FILES")
    print(f"  Target directory: {DATA_DIR}")
    print(f"  Found {len(csv_files)} daily files to ingest.")
    print("=" * 70)

    # 2. Connect to MySQL
    print("\nConnecting to MySQL...")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO seller (
            Seller_name, SKU, Region, Advertised_price,
            Marketplace, Screenshot, Live_link, Last_time_collected
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    total_inserted = 0

    # 3. Process each day's CSV file
    for idx, filepath in enumerate(csv_files, 1):
        filename = os.path.basename(filepath)
        # Extract the date from filename, e.g., '2025-12-21.csv' -> '2025-12-21'
        collected_date = os.path.splitext(filename)[0]

        file_records = []
        with open(filepath, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                seller_name = clean_str(row.get("Seller_name"))
                sku = clean_str(row.get("SKU"))
                region = clean_str(row.get("region"))
                adv_price = clean_price(row.get("adv_price"))
                marketplace = clean_str(row.get("Marketplace"))
                screenshot = clean_str(row.get("Screenshot"))
                live_link = clean_str(row.get("live_link"))

                file_records.append((
                    seller_name,
                    sku,
                    region,
                    adv_price,
                    marketplace,
                    screenshot,
                    live_link,
                    collected_date
                ))

        # Bulk insert in batches of BATCH_SIZE
        file_count = len(file_records)
        for i in range(0, file_count, BATCH_SIZE):
            batch = file_records[i : i + BATCH_SIZE]
            cursor.executemany(insert_query, batch)
            conn.commit()

        total_inserted += file_count
        print(f"  [{idx:2d}/{len(csv_files)}] Processed: {filename} ({collected_date}) -> {file_count:,} rows")

    cursor.close()
    conn.close()

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"  INGESTION COMPLETE!")
    print(f"  Total records loaded into `seller`: {total_inserted:,}")
    print(f"  Elapsed time: {elapsed:.2f} seconds")
    print("=" * 70)

if __name__ == "__main__":
    main()
