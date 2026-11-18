import os
import csv
import urllib.parse
import datetime
import scrapy
from scrapy.crawler import CrawlerProcess

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

# ==============================================================================
# 2. READ DYNAMIC INPUT PRODUCTS
# ==============================================================================
def load_input_products(filepath):
    products = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["platforms"] = [p.strip().lower() for p in row["platforms"].split(";")]
            products.append(row)
    return products

# ==============================================================================
# 3. SCRAPY ITEM DEFINITION
# ==============================================================================
class ProductPriceItem(scrapy.Item):
    Seller_name = scrapy.Field()
    SKU = scrapy.Field()
    Category = scrapy.Field()
    Region = scrapy.Field()
    Advertised_price = scrapy.Field()
    Marketplace = scrapy.Field()
    Screenshot = scrapy.Field()
    Live_link = scrapy.Field()
    Last_time_collected = scrapy.Field()
    Product_Title = scrapy.Field()
    output_filename = scrapy.Field()

# ==============================================================================
# 4. ITEM PIPELINE: ROUTER TO 9 SEPARATE CSV FILES
# ==============================================================================
class MultiCsvExportPipeline:
    def __init__(self):
        self.files = {}
        self.writers = {}
        self.fieldnames = [
            "Seller_name", "SKU", "Category", "Region", "Advertised_price",
            "Marketplace", "Screenshot", "Live_link", "Last_time_collected", "Product_Title"
        ]

    def process_item(self, item, spider=None):
        fname = item["output_filename"]
        filepath = os.path.join(OUTPUT_DIR, fname)

        if fname not in self.files:
            f = open(filepath, mode="w", newline="", encoding="utf-8")
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            self.files[fname] = f
            self.writers[fname] = writer

        row = {k: item[k] for k in self.fieldnames if k in item}
        self.writers[fname].writerow(row)
        return item

    def close_spider(self, spider=None):
        for f in self.files.values():
            f.close()

# ==============================================================================
# 5. SCRAPY SPIDER
# ==============================================================================
class MarketplaceSpider(scrapy.Spider):
    name = "marketplace_spider"

    def start_requests(self):
        products = load_input_products(INPUT_FILE)
        print(f"[*] Spider initialized with {len(products)} products to crawl.")

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

            headers = {
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.google.com/"
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
                item = ProductPriceItem()
                item["Seller_name"] = "Amazon Seller"
                item["SKU"] = sku
                item["Category"] = cat
                item["Region"] = "IN"
                item["Advertised_price"] = price
                item["Marketplace"] = "Amazon"
                item["Screenshot"] = screenshot_placeholder
                item["Live_link"] = link
                item["Last_time_collected"] = collected_at
                item["Product_Title"] = title.strip()
                item["output_filename"] = out_name
                yield item

        print(f"  [+] Amazon: Found {count} items for SKU {sku}")

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
                item = ProductPriceItem()
                item["Seller_name"] = "Flipkart Seller"
                item["SKU"] = sku
                item["Category"] = cat
                item["Region"] = "IN"
                item["Advertised_price"] = price
                item["Marketplace"] = "Flipkart"
                item["Screenshot"] = screenshot_placeholder
                item["Live_link"] = link
                item["Last_time_collected"] = collected_at
                item["Product_Title"] = title.strip()
                item["output_filename"] = out_name
                yield item

        print(f"  [+] Flipkart: Found {count} items for SKU {sku}")

# ==============================================================================
# 6. RUNNER EXECUTION
# ==============================================================================
def main():
    print("=" * 70)
    print("  SCRAPY CRAWLER (Concurrent Asynchronous Engine)")
    print(f"  Reading products from: {INPUT_FILE}")
    print(f"  Output directory:      {OUTPUT_DIR}")
    print("=" * 70)

    # Configure Scrapy settings directly in the CrawlerProcess
    settings = {
        "USER_AGENT": DEFAULT_USER_AGENT,
        "ROBOTSTXT_OBEY": False,         # Crucial: disables robots.txt blocking
        "CONCURRENT_REQUESTS": 2,        # 2 concurrent requests
        "DOWNLOAD_DELAY": 1.0,           # Respectful delay
        "ITEM_PIPELINES": {
            "__main__.MultiCsvExportPipeline": 300
        },
        "LOG_LEVEL": "WARNING",          # Keep terminal clean; warnings/errors only
        "COOKIES_ENABLED": True,
        "RETRY_TIMES": 3
    }

    process = CrawlerProcess(settings=settings)
    process.crawl(MarketplaceSpider)
    process.start()

    print("\n" + "=" * 70)
    print(f"Scrapy crawl completed! Output files saved in:")
    print(f"  {OUTPUT_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()
