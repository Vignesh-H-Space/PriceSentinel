import os
import csv
import urllib.parse
import datetime
import scrapy

# ==============================================================================
# 1. PATHS & CONFIGURATION
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "scraping_input.csv")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "scraped_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

FIELDNAMES = [
    "Seller_name", "SKU", "Category", "Region", "Advertised_price",
    "Marketplace", "Screenshot", "Live_link", "Last_time_collected", "Product_Title"
]

def append_to_csv(filename, row_dict):
    """Safely appends a scraped listing into the product's CSV file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0

    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)

def load_input_products():
    products = []
    with open(INPUT_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["platforms"] = [p.strip().lower() for p in row["platforms"].split(";")]
            products.append(row)
    return products

# ==============================================================================
# 2. THE SCRAPY SPIDER CLASS
# ==============================================================================
class MarketplaceSpider(scrapy.Spider):
    name = "marketplace_spider"

    custom_settings = {
        # Completely disable the robots.txt middleware so it can never block requests
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware": None,
        },
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": DEFAULT_USER_AGENT,
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 1.0,
        "LOG_LEVEL": "INFO",
        "COOKIES_ENABLED": True,
        "RETRY_TIMES": 3
    }

    def start_requests(self):
        products = load_input_products()
        self.logger.info(f"Loaded {len(products)} products from input file.")

        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }

        for prod in products:
            sku = prod["sku"]
            cat = prod["category"]
            query = prod["query"]
            platforms = prod["platforms"]

            safe_cat = cat.replace(" / ", "_").replace(" ", "_")
            out_name = f"{safe_cat}_{sku}.csv"

            meta_data = {
                "sku": sku,
                "category": cat,
                "query": query,
                "output_filename": out_name,
                "collected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Amazon Request
            if "amazon" in platforms:
                q_enc = urllib.parse.quote_plus(query)
                amazon_url = f"https://www.amazon.in/s?k={q_enc}"
                yield scrapy.Request(
                    url=amazon_url,
                    callback=self.parse_amazon,
                    headers=headers,
                    meta=meta_data,
                    dont_filter=True
                )

            # Flipkart Request
            if "flipkart" in platforms:
                q_enc = urllib.parse.quote_plus(query)
                flipkart_url = f"https://www.flipkart.com/search?q={q_enc}"
                yield scrapy.Request(
                    url=flipkart_url,
                    callback=self.parse_flipkart,
                    headers=headers,
                    meta=meta_data,
                    dont_filter=True
                )

    def parse_amazon(self, response):
        sku = response.meta["sku"]
        cat = response.meta["category"]
        collected_at = response.meta["collected_at"]
        out_name = response.meta["output_filename"]

        safe_cat = cat.replace(" / ", "_").replace(" ", "_")
        screenshot_placeholder = f"{safe_cat}_{sku}_amazon.png"

        cards = response.css("div[data-component-type='s-search-result']")
        count = 0

        for card in cards:
            if count >= 3:
                break

            title = card.css("h2 a span::text").get()
            if not title:
                title = card.css("h2 span::text").get()

            href = card.css("h2 a::attr(href)").get()
            link = response.urljoin(href) if href else response.url

            raw_price = card.css(".a-price .a-offscreen::text").get()
            if not raw_price:
                raw_price = card.css(".a-price-whole::text").get()

            price = None
            if raw_price:
                clean_p = raw_price.replace("₹", "").replace(",", "").replace(".", "").strip()
                try:
                    price = float(clean_p)
                except ValueError:
                    price = None

            if title and price and price > 100:
                count += 1
                row = {
                    "Seller_name": "Amazon Seller",
                    "SKU": sku,
                    "Category": cat,
                    "Region": "IN",
                    "Advertised_price": price,
                    "Marketplace": "Amazon",
                    "Screenshot": screenshot_placeholder,
                    "Live_link": link,
                    "Last_time_collected": collected_at,
                    "Product_Title": title.strip()
                }
                append_to_csv(out_name, row)

        self.logger.info(f"[Amazon] Extracted {count} listings for SKU {sku}")

    def parse_flipkart(self, response):
        sku = response.meta["sku"]
        cat = response.meta["category"]
        collected_at = response.meta["collected_at"]
        out_name = response.meta["output_filename"]

        safe_cat = cat.replace(" / ", "_").replace(" ", "_")
        screenshot_placeholder = f"{safe_cat}_{sku}_flipkart.png"

        cards = response.css("div.tUxRFH, div._75nlfW, div.slAVV4, div.cPHDOP, div[data-id]")
        count = 0

        for card in cards:
            if count >= 3:
                break

            title = card.css("div.KzDlHZ::text, div._4rR01T::text, a.wjcEIp::text, a.s1Q9rs::text").get()
            if not title:
                title = card.css("img::attr(alt)").get()

            raw_price = card.css("div.Nx9bqj::text, div._30jeq3::text").get()
            price = None
            if raw_price:
                clean_p = raw_price.replace("₹", "").replace(",", "").strip()
                try:
                    price = float(clean_p)
                except ValueError:
                    price = None

            href = card.css("a[href*='/p/']::attr(href)").get()
            if not href:
                href = card.css("a::attr(href)").get()
            link = response.urljoin(href) if href else response.url

            if title and price and price > 50:
                count += 1
                row = {
                    "Seller_name": "Flipkart Seller",
                    "SKU": sku,
                    "Category": cat,
                    "Region": "IN",
                    "Advertised_price": price,
                    "Marketplace": "Flipkart",
                    "Screenshot": screenshot_placeholder,
                    "Live_link": link,
                    "Last_time_collected": collected_at,
                    "Product_Title": title.strip()
                }
                append_to_csv(out_name, row)

        self.logger.info(f"[Flipkart] Extracted {count} listings for SKU {sku}")
