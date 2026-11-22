# Price Sentinel
### Automated E-Commerce Price Monitoring & MAP Compliance Engine

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![Web Scraping](https://img.shields.io/badge/Scraping-Selenium%20%7C%20Playwright%20%7C%20BS4-green.svg)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An enterprise-grade, end-to-end Brand Protection and Market Surveillance data pipeline designed for global electronics manufacturers (e.g., HP, Dell, Lenovo). The system monitors e-commerce marketplaces (Amazon, Flipkart, etc.), identifies unauthorized seller undercutting, calculates Minimum Advertised Price (MAP) and Lowest Possible Price (LPP) violations, and automatically drafts formal legal compliance notices.

---

## 📌 Executive Summary & Key Results

- **148,000+ Market Observations Monitored:** Ingested daily marketplace crawls across 15 consecutive dates.
- **Multi-Format Master Catalog:** Ingested product catalogs and pricing logic from XML, JSON, YAML, and Excel spreadsheets into 6 relational MySQL tables.
- **3 Web Scraping Paradigms Implemented:** Built parallel scraping engines in **BeautifulSoup**, **Selenium WebDriver**, and **Microsoft Playwright** to track live pricing, handle dynamic DOM rendering, and capture evidence screenshots.
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
 │  └── Playwright: Modern Chromium engine + dynamic search URLs   │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │               STAGE 3: BATCH OBSERVATIONS INGESTION             │
 │  Bulk ingested 148,000+ daily seller records (15 days) into     │
 │  the `seller` table using 5,000-row batch commits (<15 seconds) │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │               STAGE 4: ANALYTICAL INTEGRATION                   │
 │  Multi-table join unifying Market Data + Pricing Master Catalog │
 │  Populates the unified `price_monitoring` table                 │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │               STAGE 5: VIOLATION DETECTION & REMEDIATION        │
 │  ├── Business Rule Engine: LPP Trigger + Promotional Exemptions │
 │  ├── `violation` Table (122,823 infractions classified)         │
 │  ├── Automated Legal Warning Notice (Word .docx with Top 10)    │
 │  └── Full Itemized Audit Ledger Export (.csv)                   │
 └─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Repository Overview

```
Price-Sentinel/
├── README.md                                  # Main repository overview & quickstart
│
├── Week 1/                                    # Architecture blueprints & data dictionary
│
├── Week 2/
│   ├── Resources/                             # Raw product catalogs (XML, JSON, YAML, Excel)
│   ├── Task 2 - Populating Tables/            # Database schema & catalog ingestion scripts
│   └── Task 3 - Web Scraping/                 # BeautifulSoup, Selenium, and Playwright scrapers
│
└── Week 3/
    ├── Resources/                             # 15 daily marketplace observation snapshots
    ├── Task 4 - Populating Seller Data/       # High-throughput batch ingestion pipeline
    ├── Task 5 - Populating Price Monitoring/  # Multi-table price monitoring SQL views
    └── Task 6 - Violation/                    # Violation rule engine, Word notice & CSV export
```

---

## ⚙️ Core Technical Highlights

### 1. Master Catalog & Relational Data Engineering
- Handled heterogeneous non-standard formats: XML entities, JSON-lines, nested YAML, and multi-sheet Excel files.
- Configurable **Lowest Possible Price (LPP)** formula:
  $$\text{Reduction} = \text{MAP} \times \text{Discount Rate}$$
  $$\text{LPP} = \text{MAP} - \text{Reduction} = \text{MAP} \times (1 - \text{Discount Rate})$$
  *(Discount rates dynamically driven by brand: HP vs. Dell across 7 subcategories).*

### 2. Multi-Engine Web Scraping & Dynamic DOM Automation
- **BeautifulSoup:** High-speed HTTP requests with randomized User-Agents and fallback payloads for lightweight static extraction.
- **Selenium WebDriver:** Automated real Chrome sessions, scrolled past top video ads, extracted live prices, and saved verified `.png` audit screenshots.
- **Playwright:** Leveraged Chromium engine, bypassed Flipkart's login modal via direct search URL navigation, and used `text_content()` to reliably extract prices from hidden DOM elements.

### 3. High-Throughput Batch Ingestion
- Automated collection date extraction directly from file names (`2025-12-21.csv` $\rightarrow$ `2025-12-21`).
- Implemented **5,000-row batch insertion** with `executemany()`, loading all **148,000+ records in ~12 seconds**.

### 4. Violation Rule Engine & Compliance Floor Logic
- **Promotional Exemption Rule:** If a SKU belongs to the authorized 100 promotional SKUs, standard LPP/MAP checks are waived. The product is **compliant** as long as $\text{Advertised Price} \ge \text{Promotional Price}$.
- **Standard SKU Rule:** If a product is not on authorized promotion, selling below LPP triggers an immediate **`LPP Breach (Critical)`**.
- **Currency Normalization:** Converted $10 USD flat LaserJet discount to its local currency equivalent (₹830 off MAP) to align with catalog pricing.

---

## 🚀 How to Run

### Prerequisites
- **Python 3.10+**
- **MySQL Server 8.0**

### 1. Install Dependencies
```bash
pip install mysql-connector-python pyyaml openpyxl requests beautifulsoup4 selenium playwright webdriver-manager python-docx
playwright install chromium
```

### 2. Database & Pipeline Execution
1. **Catalog Setup:** Execute the database scripts to populate the 6 master tables in MySQL.
2. **Web Scraping:** Run any of the scrapers (e.g. `python Visual_Price_Scraper.py` or `python Playwright_Price_Scraper.py`).
3. **Seller Ingestion:** Run `python "Populate Seller Table using Python.py"` to ingest the 148,000+ daily observations.
4. **Analytical Integration:** Execute `Populate Price Monitoring Table.sql` in MySQL to construct the unified monitoring view.
5. **Violation Detection & Notices:** Run `python Generate_Violations_And_Notice_Doc.py` to evaluate violations, update the database, and generate the executive notice.

---

## 📜 Deliverables Generated

1. **MySQL Database `map_project`:** Relational schema storing master catalogs, daily observations, analytical views, and detected violations.
2. **`MAP_Violation_Notice_Email.docx`:** Professional legal notice featuring executive aggregate metrics, remediation instructions, and an embedded Top 10 unique product violation table.
3. **`Full_Marketplace_Violations_Ledger.csv`:** Complete itemized dataset containing all 122,823 violation records for compliance audit trails.
