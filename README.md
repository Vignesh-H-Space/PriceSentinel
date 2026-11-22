# Minimum Advertised Price (MAP) Monitoring & Compliance Pipeline

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![Web Scraping](https://img.shields.io/badge/Scraping-Selenium%20%7C%20Playwright%20%7C%20Scrapy%20%7C%20BS4-green.svg)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An enterprise-grade, end-to-end Brand Protection and Market Surveillance data pipeline designed for global electronics manufacturers (e.g., HP, Dell). The system monitors e-commerce marketplaces (Amazon, Flipkart, eBay, etc.), identifies unauthorized seller undercutting, calculates Minimum Advertised Price (MAP) and Lowest Possible Price (LPP) violations, and automatically drafts formal legal compliance notices.

---

## 📌 Executive Summary & Key Results

- **148,000+ Market Observations Monitored:** Ingested daily marketplace crawls across 15 consecutive dates.
- **Multi-Format Master Catalog:** Ingested product catalogs and pricing logic from XML, JSON, YAML, and Excel spreadsheets into 6 relational MySQL tables.
- **4 Web Scraping Paradigms Implemented:** Built parallel scraping engines in **BeautifulSoup**, **Selenium WebDriver**, **Microsoft Playwright**, and **Scrapy** to track live pricing and capture evidence screenshots.
- **Automated Violation Engine:** Detected **122,823 total price infractions** (114,797 Critical LPP Breaches and 8,026 Promotional Floor Breaches), revealing an overall channel compliance rate of only **17.0%**.
- **Automated Legal Remediation:** Programmatically generates Word document Cease & Desist notices (`.docx`) containing verified evidence tables and exports complete audit ledgers (`.csv`).

---

## 🏗️ System Architecture

```
                                 DATA SOURCES
  ┌──────────────┬──────────────┬──────────────┬───────────────────┐
  │   SKU.xml    │ PL,SKU.json  │ MAP_PL.yaml  │ LPP / Promo Excel │
  └──────┬───────┴──────┬───────┴──────┬───────┴─────────┬─────────┘
         │              │              │                 │
         ▼              ▼              ▼                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │               STAGE 1: MASTER CATALOG DATABASE (MySQL)          │
 │  ├── sku (Product Numbers & SKU catalog)                        │
 │  ├── pl (Product Line & Subcategory derivation)                 │
 │  ├── price_list (MAP price & calculated LPP floor)              │
 │  ├── seller_mapping (Raw sellers -> Clean Homologated Brands)   │
 │  ├── category_mapping (PC, Supply, Print Hardware)              │
 │  └── promotion (Q4 seasonal promotional discount logic)         │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │               STAGE 2: WEB SCRAPING & MARKET MONITORING         │
 │  ├── BeautifulSoup: High-speed static HTTP extraction           │
 │  ├── Selenium: Real Chrome automation + full-page screenshots   │
 │  ├── Playwright: Modern Chromium engine + dynamic search URLs   │
 │  └── Scrapy: Asynchronous concurrent crawling framework         │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │               STAGE 3: BATCH SELLER INGESTION (Task 4)          │
 │  Bulk ingested 148,000+ daily seller records (15 days) into     │
 │  the `seller` table using 5,000-row batch commits (<15 seconds) │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │               STAGE 4: ANALYTICAL INTEGRATION (Task 5)          │
 │  Multi-table join unifying Market Data + Pricing Master Catalog │
 │  Populates the unified `price_monitoring` table                 │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │               STAGE 5: VIOLATION DETECTION & REMEDIATION (Task 6)│
 │  ├── Business Rule Engine: LPP Trigger + Promotional Exemptions │
 │  ├── `violation` Table (122,823 infractions classified)         │
 │  ├── Automated Legal Warning Notice (Word .docx with Top 10)    │
 │  └── Full Itemized Audit Ledger Export (.csv)                   │
 └─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Repository Structure

```
D:\Github\MAP\
├── README.md                                 # Main repository overview & documentation
├── PROJECT_WALKTHROUGH_AND_REFERENCE.docx    # Deep technical guide & interview reference
│
├── Week 1\
│   └── Resources\
│       ├── Data Dictionary.docx              # Official data dictionary & entity schemas
│       └── Project Architecture.png          # High-level architecture blueprint
│
├── Week 2\
│   ├── Resources\                            # Master catalog source files
│   │   ├── SKU.xml                           # Base catalog (1,598 items)
│   │   ├── PL,SKU.json                       # Product Line mapping
│   │   ├── MAP, PL, SKU .yaml                # MAP pricing catalog
│   │   ├── LPP Calculation.xlsx              # Brand & category discount percentages
│   │   ├── Promotion SKU.xlsx                # 100 promotional SKUs & seasonal offers
│   │   └── Seller Details.xlsx               # 903 seller homologation mappings
│   │
│   ├── Task 2 - Populating Tables\           # Master database setup scripts
│   │   ├── Create SKU Table.sql
│   │   ├── Populate PL Table using Python.py
│   │   ├── Populate Price List Table using Python.py
│   │   ├── Populate Seller Mapping Table using Python.py
│   │   ├── Populate Category Mapping Table using Python.py
│   │   └── Populate Promotion Table using Python.py
│   │
│   └── Task 3 - Web Scraping\                # 4 distinct scraping implementations
│       ├── BeautifulSoup_Scraper\            # Silent HTTP scraping (requests + BS4)
│       │   ├── Marketplace_Price_Scraper.py
│       │   └── scraped_data\                 # 9 product CSVs
│       ├── Selenium_Scraper\                 # Visual browser scraper (Selenium + Chrome)
│       │   ├── scraping_input.csv            # Dynamic input configuration
│       │   ├── Visual_Price_Scraper.py
│       │   └── scraped_data\                 # 9 product CSVs + 18 PNG screenshots
│       ├── Playwright_Scraper\               # Modern Chromium scraper (Playwright)
│       │   ├── scraping_input.csv
│       │   ├── Playwright_Price_Scraper.py
│       │   └── scraped_data\                 # 9 product CSVs + 18 PNG screenshots
│       └── Scrapy_Scraper\                   # Asynchronous concurrent crawler
│           ├── scraping_input.csv
│           ├── run_scrapy_scraper.py
│           └── scraped_data\
│
└── Week 3\
    ├── Resources\
    │   └── Seller Data\                      # 15 daily marketplace CSVs (~148,000 rows)
    │       ├── 2025-12-21.csv ... 2026-01-05.csv
    │
    ├── Task 4 - Populating Seller Data\      # High-speed bulk ingestion
    │   ├── Create Seller Table.sql
    │   └── Populate Seller Table using Python.py
    │
    ├── Task 5 - Populating Price Monitoring Table\  # Master relational integration
    │   └── Populate Price Monitoring Table.sql
    │
    └── Task 6 - Violation\                   # Rule engine, report & notice generation
        ├── Generate_Violations_And_Notice_Doc.py
        ├── MAP_Violation_Notice_Email.docx   # Generated Cease & Desist Notice
        └── Full_Marketplace_Violations_Ledger.csv # All 122,823 violation records
```

---

## ⚙️ Core Technical Highlights

### 1. Multi-Format Data Engineering (Task 2)
- Handled non-standard formats: XML entities, JSON-lines, nested YAML, and multi-sheet Excel files.
- Configurable **Lowest Possible Price (LPP)** formula:
  $$\text{Reduction} = \text{MAP} \times \text{Discount Rate}$$
  $$\text{LPP} = \text{MAP} - \text{Reduction} = \text{MAP} \times (1 - \text{Discount Rate})$$
  *(Discount rates dynamically driven by brand: HP vs. Dell across 7 subcategories).*

### 2. Four Web Scraping Implementations (Task 3)
- **BeautifulSoup:** High-speed HTTP requests with randomized User-Agents and fallback payloads.
- **Selenium WebDriver:** Automated real Chrome sessions, scrolled past top video ads, extracted live prices, and saved verified `.png` screenshots.
- **Playwright:** Leveraged Chromium engine, bypassed Flipkart's login modal via direct search URL navigation, and used `text_content()` for hidden DOM tags.
- **Scrapy:** Concurrent asynchronous crawling with robots.txt middleware management.

### 3. High-Speed Bulk Loading (Task 4)
- Automated extraction of collection dates directly from file names (`2025-12-21.csv` $\rightarrow$ `2025-12-21`).
- Implemented **5,000-row batch insertion** with `executemany()`, loading all **148,000+ records in ~12 seconds**.

### 4. Custom Business Rule Engine (Task 6)
- **Promotional Exemption Rule:** If a SKU belongs to the authorized 100 promotional SKUs, standard LPP/MAP checks are waived. The product is **compliant** as long as $\text{Advertised Price} \ge \text{Promotional Price}$.
- **Standard SKU Rule:** If a product is not on authorized promotion, selling below LPP triggers an immediate **`LPP Breach (Critical)`**.

---

## 🚀 How to Run the Project

### Prerequisites
- **Python 3.10+**
- **MySQL Server 8.0**
- Install dependencies:
  ```bash
  pip install mysql-connector-python pyyaml openpyxl requests beautifulsoup4 selenium playwright webdriver-manager scrapy python-docx
  playwright install chromium
  ```

### Step-by-Step Execution
1. **Master Catalog Setup (Task 2):**
   Run the scripts in `Week 2\Task 2 - Populating Tables\` to populate the 6 base tables.
2. **Web Scraping (Task 3):**
   ```bash
   cd "Week 2\Task 3\Selenium_Scraper"
   python Visual_Price_Scraper.py
   ```
3. **Seller Data Bulk Ingestion (Task 4):**
   ```bash
   cd "Week 3\Task 4 - Populating Seller Data"
   python "Populate Seller Table using Python.py"
   ```
4. **Price Monitoring Integration (Task 5):**
   Execute `Populate Price Monitoring Table.sql` in MySQL Workbench.
5. **Violation Detection & Notice Generation (Task 6):**
   ```bash
   cd "Week 3\Task 6 - Violation"
   python Generate_Violations_And_Notice_Doc.py
   ```

---

## 📜 Deliverables Generated

1. **MySQL Database `map_project`:** 8 relational tables (`sku`, `pl`, `price_list`, `seller_mapping`, `category_mapping`, `promotion`, `seller`, `price_monitoring`, `violation`).
2. **`MAP_Violation_Notice_Email.docx`:** Professional legal notice featuring executive aggregate metrics, remediation instructions, and an embedded Top 10 Evidence Table.
3. **`Full_Marketplace_Violations_Ledger.csv`:** Full dataset of all 122,823 itemized violation records.
4. **`PROJECT_WALKTHROUGH_AND_REFERENCE.docx`:** Comprehensive technical deep-dive and interview guide.

---

## 👤 Author
**MAP Brand Protection & Compliance Data Engineering Project**
