import os
import time
import datetime
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCX_PATH = os.path.join(SCRIPT_DIR, "MAP_Violation_Notice_Email.docx")

# ==============================================================================
# 2. STEP 1: CREATE VIOLATION TABLE & POPULATE FROM PRICE_MONITORING
# ==============================================================================
def populate_violation_table(conn):
    cursor = conn.cursor()
    print("[1/3] Creating `violation` table in MySQL...")

    cursor.execute("DROP TABLE IF EXISTS violation;")
    create_table_sql = """
        CREATE TABLE violation (
            Violation_ID INT AUTO_INCREMENT PRIMARY KEY,
            SKU VARCHAR(100),
            Violation_date DATE,
            Category VARCHAR(100),
            Sub_category VARCHAR(100),
            Marketplace VARCHAR(100),
            Region VARCHAR(50),
            seller_name VARCHAR(255),
            homologated_name VARCHAR(255),
            MAP_Price DECIMAL(12, 4),
            LPP DECIMAL(12, 4),
            Promotional_price DECIMAL(12, 4),
            Advertised_price DECIMAL(12, 4),
            Price_Difference DECIMAL(12, 4),
            Violation_Percentage DECIMAL(6, 2),
            Violation_Type VARCHAR(50),
            Severity_Level VARCHAR(20),
            INDEX idx_v_sku (SKU),
            INDEX idx_v_seller (seller_name),
            INDEX idx_v_date (Violation_date)
        );
    """
    cursor.execute(create_table_sql)

    print("[2/3] Extracting and calculating violations based on promotional exemption rules...")
    insert_sql = """
        INSERT INTO violation (
            SKU,
            Violation_date,
            Category,
            Sub_category,
            Marketplace,
            Region,
            seller_name,
            homologated_name,
            MAP_Price,
            LPP,
            Promotional_price,
            Advertised_price,
            Price_Difference,
            Violation_Percentage,
            Violation_Type,
            Severity_Level
        )
        SELECT 
            SKU,
            Violation_date,
            Category,
            Sub_category,
            Marketplace,
            Region,
            seller_name,
            homologated_name,
            MAP_Price,
            LPP,
            Promotional_price,
            Advertised_price,
            -- Price difference against the effective allowed floor
            ROUND(
                CASE 
                    WHEN Promotional_price IS NOT NULL THEN (Promotional_price - Advertised_price)
                    ELSE (MAP_Price - Advertised_price)
                END, 4
            ) AS Price_Difference,
            -- Violation percentage against the effective allowed floor
            ROUND(
                (
                    CASE 
                        WHEN Promotional_price IS NOT NULL THEN (Promotional_price - Advertised_price)
                        ELSE (MAP_Price - Advertised_price)
                    END
                    / 
                    CASE 
                        WHEN Promotional_price IS NOT NULL THEN Promotional_price
                        ELSE MAP_Price
                    END
                ) * 100, 2
            ) AS Violation_Percentage,
            -- Violation Classification:
            -- 1. If in Promotional SKUs: Only violates if below Promotional_price (LPP is ignored!)
            -- 2. If NOT in Promotional SKUs: Flags LPP Breach or MAP Violation
            CASE 
                WHEN Promotional_price IS NOT NULL THEN 'Promotional MAP Breach'
                WHEN Advertised_price < LPP THEN 'LPP Breach'
                ELSE 'MAP Violation'
            END AS Violation_Type,
            -- Severity Classification
            CASE 
                WHEN Promotional_price IS NOT NULL THEN 'HIGH'
                WHEN Advertised_price < LPP THEN 'CRITICAL'
                ELSE 'HIGH'
            END AS Severity_Level
        FROM price_monitoring
        WHERE Advertised_price > 0
          AND (
              -- Case 1: SKU is on Promotion -> ONLY a violation if Advertised_price < Promotional_price!
              -- (If Advertised_price >= Promotional_price, NO VIOLATION regardless of LPP!)
              (Promotional_price IS NOT NULL AND Advertised_price < Promotional_price)
              OR
              -- Case 2: SKU is NOT on Promotion -> Violates if Advertised_price < MAP_Price
              (Promotional_price IS NULL AND Advertised_price < MAP_Price)
          );
    """
    cursor.execute(insert_sql)
    conn.commit()

    total_inserted = cursor.rowcount
    print(f"      -> Successfully inserted {total_inserted:,} violation records into MySQL `violation` table.")

    # Fetch top 10 unique product SKUs with highest shortfall (prevents same SKU repeating)
    query_samples = """
        WITH RankedViolations AS (
            SELECT 
                Violation_date,
                homologated_name,
                seller_name,
                Marketplace,
                SKU,
                Sub_category,
                MAP_Price,
                COALESCE(Promotional_price, MAP_Price) AS Effective_Price,
                Advertised_price,
                Price_Difference,
                Violation_Percentage,
                Severity_Level,
                ROW_NUMBER() OVER (PARTITION BY SKU ORDER BY Price_Difference DESC) as rn
            FROM violation
        )
        SELECT 
            Violation_date,
            homologated_name,
            seller_name,
            Marketplace,
            SKU,
            Sub_category,
            MAP_Price,
            Effective_Price,
            Advertised_price,
            Price_Difference,
            Violation_Percentage,
            Severity_Level
        FROM RankedViolations
        WHERE rn = 1
        ORDER BY Price_Difference DESC
        LIMIT 10;
    """
    cursor.execute(query_samples)
    sample_violations = cursor.fetchall()

    cursor.close()
    return total_inserted, sample_violations

# ==============================================================================
# 3. STEP 2: CREATE WORD DOCUMENT (.DOCX) FOR FORMAL VIOLATION NOTICE
# ==============================================================================
def create_violation_word_document(total_violations, sample_violations):
    print("[3/3] Generating formal Violation Notice document (Word format)...")
    
    try:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
    except ImportError:
        print("\n[Notice] 'python-docx' library is not yet installed.")
        print("         Please run: pip install python-docx")
        print("         Then re-run this script to generate the Word document.\n")
        return

    doc = Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # 1. Header Banner
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("BRAND PROTECTION & CHANNEL COMPLIANCE DIVISION")
    title_run.font.size = Pt(14)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(31, 78, 121)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run("FORMAL NOTICE OF MINIMUM ADVERTISED PRICE (MAP) POLICY VIOLATION")
    sub_run.font.size = Pt(12)
    sub_run.font.bold = True
    sub_run.font.color.rgb = RGBColor(192, 0, 0)  # Red alert header

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 2. Email / Memo Metadata Block
    meta_p = doc.add_paragraph()
    meta_p.add_run("Date: ").bold = True
    meta_p.add_run(f"{datetime.date.today().strftime('%B %d, %Y')}\n")
    meta_p.add_run("To: ").bold = True
    meta_p.add_run("Authorized Reseller Partner & Marketplace Store Management\n")
    meta_p.add_run("From: ").bold = True
    meta_p.add_run("Brand Integrity & Authorized Channel Governance Office\n")
    meta_p.add_run("Subject: ").bold = True
    meta_p.add_run("[ACTION REQUIRED] URGENT: Official Cease & Desist / MAP Price Rectification Notice\n")
    meta_p.add_run("Status: ").bold = True
    status_run = meta_p.add_run("POLICY INFRACTION DETECTED - 24-HOUR CURE PERIOD")
    status_run.font.color.rgb = RGBColor(192, 0, 0)
    status_run.font.bold = True

    doc.add_paragraph("—" * 55)

    # 3. Formal Notice Body
    p1 = doc.add_paragraph()
    p1.add_run(
        "Dear Store Manager / Channel Partner,\n\n"
        "This official notice is transmitted by the Brand Integrity and Market Monitoring Unit. "
        "Through our continuous automated price monitoring systems, your online storefronts have been "
        "identified as advertising products at prices strictly below the established Minimum Advertised Price (MAP) "
        "and Lowest Possible Price (LPP) policy thresholds.\n\n"
        f"A total of {total_violations:,} violation incidents were logged during our latest market surveillance audit across regional marketplace channels. "
        "Advertising products below our authorized thresholds constitutes a material breach of your Reseller Agreement and undermines fair market practices."
    )

    # 4. Evidence Table
    doc.add_heading("Summary Evidence of Recent Price Infractions", level=2)
    evidence_desc = doc.add_paragraph(
        "The following schedule details verified price infractions captured directly from marketplace channels:"
    )

    table = doc.add_table(rows=1, cols=7)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header Row
    headers = ["Date", "Seller Name", "Marketplace", "SKU", "Advertised", "Authorized Floor", "Shortfall"]
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.bold = True
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(255, 255, 255)

    # Color Table Header (Dark Blue)
    for cell in hdr_cells:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), '1F4E79')
        tcPr.append(shd)

    # Populate Sample Rows
    for row in sample_violations:
        v_date, h_name, s_name, mkt, sku, subcat, map_p, eff_p, adv_p, diff_p, v_pct, sev = row
        row_cells = table.add_row().cells
        row_cells[0].text = str(v_date)
        row_cells[1].text = str(h_name or s_name)[:20]
        row_cells[2].text = str(mkt)
        row_cells[3].text = str(sku)
        row_cells[4].text = f"₹{adv_p:,.2f}"
        row_cells[5].text = f"₹{eff_p:,.2f}"
        row_cells[6].text = f"-₹{diff_p:,.2f} ({v_pct}%)"

        for idx, c in enumerate(row_cells):
            p = c.paragraphs[0]
            if idx in [4, 5, 6]:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            for run in p.runs:
                run.font.size = Pt(8.5)
                if idx == 6:
                    run.font.color.rgb = RGBColor(192, 0, 0)
                    run.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 5. Remediation Mandate & Penalty Warning
    doc.add_heading("Mandatory Remediation Actions (24-Hour Notice)", level=2)
    p_remedy = doc.add_paragraph()
    p_remedy.add_run(
        "To restore compliance and avoid commercial escalations, you must execute the following actions immediately:\n\n"
    )
    doc.add_paragraph("1. Adjust Advertised Pricing: Immediately update your active marketplace listings to reflect authorized MAP thresholds or above.", style='List Number')
    doc.add_paragraph("2. Audit Automated Re-pricing Algorithms: Ensure any third-party repricing software does not undercut authorized floors.", style='List Number')
    doc.add_paragraph("3. Confirmation of Cure: Reply to this notice within twenty-four (24) hours verifying price rectification.", style='List Number')

    p_warn = doc.add_paragraph()
    p_warn.paragraph_format.space_before = Pt(8)
    warn_run = p_warn.add_run(
        "CONSEQUENCES OF NON-COMPLIANCE:\n"
        "Failure to correct the designated pricing within 24 hours will result in immediate escalation, including: "
        "(a) Revocation of Authorized Partner Status, (b) Cancellation of pending purchase orders, "
        "(c) Formal brand de-listing requests submitted directly to the respective marketplace governance bodies, and "
        "(d) Referral to Corporate Legal Counsel for breach of contract damages."
    )
    warn_run.font.bold = True
    warn_run.font.size = Pt(9.5)
    warn_run.font.color.rgb = RGBColor(192, 0, 0)

    # 6. Sign-off
    p_sign = doc.add_paragraph()
    p_sign.paragraph_format.space_before = Pt(14)
    p_sign.add_run(
        "Sincerely,\n\n"
        "Corporate Brand Protection & Pricing Integrity Office\n"
        "Global Channel Compliance Directorate\n"
        "Email: compliance@brandprotection-monitoring.com\n"
    )

    doc.save(DOCX_PATH)
    print(f"      -> Word Document successfully generated and saved at:")
    print(f"         {DOCX_PATH}")

# ==============================================================================
# 4. MAIN ENTRYPOINT
# ==============================================================================
def main():
    print("=" * 70)
    print("  TASK 6: POPULATING VIOLATIONS TABLE & DRAFTING VIOLATION NOTICE DOC")
    print("=" * 70)

    conn = mysql.connector.connect(**db_config)
    try:
        total_violations, sample_violations = populate_violation_table(conn)
        create_violation_word_document(total_violations, sample_violations)
    finally:
        conn.close()

    print("=" * 70)
    print("  TASK 6 EXECUTION COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    main()
