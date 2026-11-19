# Packages to Install
# pip install playwright
# playwright install chromium

import os
import csv
import time
import datetime
import urllib.parse
from playwright.sync_api import sync_playwright

# ==============================================================================
# 1. PATHS & DIRECTORIES
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "scraping_input.csv")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "scraped_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================================================================
# 2. READ DYNAMIC INPUT FILE
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
# 3. PLAYWRIGHT AMAZON SCRAPER (DIRECT URL NAVIGATION + TEXT_CONTENT)
# ==============================================================================
def scrape_amazon_playwright(page, query, sku, category, top_n=3):
    print(f"    [Playwright - Amazon] Searching query: {query}...")
    results = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_cat = category.replace(" / ", "_").replace(" ", "_")
    screenshot_name = f"{safe_cat}_{sku}_amazon.png"
    screenshot_path = os.path.join(OUTPUT_DIR, screenshot_name)

    encoded_q = urllib.parse.quote_plus(query)
    search_url = f"https://www.amazon.in/s?k={encoded_q}"

    try:
        # Navigate directly to the search URL (bypasses homepage search typing & popups)
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        # Scroll down slightly to trigger rendering of product images & prices
        page.mouse.wheel(0, 500)
        time.sleep(1.5)

        # Capture search results screenshot
        page.screenshot(path=screenshot_path)
        print(f"    [Playwright - Amazon] Screenshot captured: {screenshot_name}")

        # Locate product cards
        cards = page.locator("div[data-component-type='s-search-result']").all()

        for card in cards:
            if len(results) >= top_n:
                break

            title = None
            price = None
            link = None

            # 1. Title
            t_loc = card.locator("h2 a span, h2 span, h2 a").first
            if t_loc.count() > 0:
                title = (t_loc.text_content() or "").strip()

            # 2. Link
            l_loc = card.locator("h2 a").first
            if l_loc.count() > 0:
                href = l_loc.get_attribute("href")
                if href:
                    link = href if href.startswith("http") else "https://www.amazon.in" + href

            # 3. Price (Use text_content to read .a-offscreen and .a-price-whole)
            p_loc = card.locator(".a-price .a-offscreen, .a-price-whole").first
            if p_loc.count() > 0:
                raw_price = (p_loc.text_content() or "").replace("₹", "").replace(",", "").replace(".", "").strip()
                try:
                    price = float(raw_price)
                except ValueError:
                    price = None

            # Filter valid products (ignore cheap minor accessories)
            if title and price and price > 100:
                results.append({
                    "Seller_name": "Amazon Seller",
                    "SKU": sku,
                    "Category": category,
                    "Region": "IN",
                    "Advertised_price": price,
                    "Marketplace": "Amazon",
                    "Screenshot": screenshot_name,
                    "Live_link": link or search_url,
                    "Last_time_collected": collected_at,
                    "Product_Title": title
                })

    except Exception as e:
        print(f"    [Playwright - Amazon Warning/Error]: {e}")
        try:
            page.screenshot(path=screenshot_path)
        except Exception:
            pass

    print(f"    [Playwright - Amazon] Extracted {len(results)} listings.")
    return results

# ==============================================================================
# 4. PLAYWRIGHT FLIPKART SCRAPER (DIRECT URL - BYPASSES LOGIN POPUP 100%)
# ==============================================================================
def scrape_flipkart_playwright(page, query, sku, category, top_n=3):
    print(f"    [Playwright - Flipkart] Searching query: {query}...")
    results = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_cat = category.replace(" / ", "_").replace(" ", "_")
    screenshot_name = f"{safe_cat}_{sku}_flipkart.png"
    screenshot_path = os.path.join(OUTPUT_DIR, screenshot_name)

    encoded_q = urllib.parse.quote_plus(query)
    search_url = f"https://www.flipkart.com/search?q={encoded_q}"

    try:
        # Navigating directly to search URL completely bypasses the homepage login dialog
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        # Dismiss login dialog if it ever appears over search page
        try:
            close_btn = page.locator("span._30XB9F, button._2KpZ6l._2doB4z").first
            if close_btn.is_visible():
                close_btn.click()
                time.sleep(0.5)
        except Exception:
            pass

        # Scroll down slightly to trigger lazy-loaded cards
        page.mouse.wheel(0, 400)
        time.sleep(1.5)

        page.screenshot(path=screenshot_path)
        print(f"    [Playwright - Flipkart] Screenshot captured: {screenshot_name}")

        # Locate product cards: works for both List view (Laptops) and Grid view (Toners/Printers)
        cards = page.locator("div._75nlfW, div.tUxRFH, div.slAVV4, div.cPHDOP, div[data-id]").all()
        if not cards:
            cards = page.locator("//a[contains(@href, '/p/') and .//*[contains(text(), '₹')]]").all()

        for card in cards:
            if len(results) >= top_n:
                break

            title = None
            price = None
            link = None

            # 1. Price: Flipkart uses div.Nx9bqj and div._30jeq3
            p_loc = card.locator("div.Nx9bqj, div._30jeq3").first
            if p_loc.count() > 0:
                raw_txt = (p_loc.text_content() or "").replace("₹", "").replace(",", "").strip()
                try:
                    price = float(raw_txt)
                except ValueError:
                    price = None
            else:
                # Fallback to any ₹ text
                p_any = card.locator(".//*[contains(text(), '₹')]").first
                if p_any.count() > 0:
                    raw_txt = (p_any.text_content() or "").strip()
                    clean_num = raw_txt.split("₹")[-1].split()[0].replace(",", "").strip()
                    try:
                        val = float(clean_num)
                        if val > 50:
                            price = val
                    except ValueError:
                        pass

            # 2. Title: Flipkart uses div.KzDlHZ, div._4rR01T, a.wjcEIp, a.s1Q9rs
            t_loc = card.locator("div.KzDlHZ, div._4rR01T, a.wjcEIp, a.s1Q9rs, a.WKTcLC").first
            if t_loc.count() > 0:
                title = (t_loc.text_content() or "").strip()
            else:
                img_loc = card.locator("img[alt]").first
                if img_loc.count() > 0:
                    alt_txt = img_loc.get_attribute("alt")
                    if alt_txt and len(alt_txt) > 5:
                        title = alt_txt.strip()

            # 3. Link
            l_loc = card.locator("a[href*='/p/']").first
            if l_loc.count() == 0:
                l_loc = card.locator("a[href]").first
            if l_loc.count() > 0:
                href = l_loc.get_attribute("href")
                if href:
                    link = href if href.startswith("http") else "https://www.flipkart.com" + href

            if title and price:
                results.append({
                    "Seller_name": "Flipkart Seller",
                    "SKU": sku,
                    "Category": category,
                    "Region": "IN",
                    "Advertised_price": price,
                    "Marketplace": "Flipkart",
                    "Screenshot": screenshot_name,
                    "Live_link": link or search_url,
                    "Last_time_collected": collected_at,
                    "Product_Title": title
                })

    except Exception as e:
        print(f"    [Playwright - Flipkart Warning/Error]: {e}")
        try:
            page.screenshot(path=screenshot_path)
        except Exception:
            pass

    print(f"    [Playwright - Flipkart] Extracted {len(results)} listings.")
    return results

# ==============================================================================
# 5. CSV SAVER
# ==============================================================================
def save_to_csv(records, filename):
    fieldnames = [
        "Seller_name", "SKU", "Category", "Region", "Advertised_price",
        "Marketplace", "Screenshot", "Live_link", "Last_time_collected", "Product_Title"
    ]
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)
    print(f"  --> [Saved CSV] {len(records)} rows to: {filename}")

# ==============================================================================
# 6. MAIN ORCHESTRATION
# ==============================================================================
def main():
    print("=" * 70)
    print("  PLAYWRIGHT PRICE SCRAPER (Direct URL Navigation + Resilient Parser)")
    print(f"  Reading products from: {INPUT_FILE}")
    print(f"  Saving results in:     {OUTPUT_DIR}")
    print("=" * 70)

    products = load_input_products(INPUT_FILE)
    print(f"\nLoaded {len(products)} products to scrape.\n")

    with sync_playwright() as p:
        # Launch Chromium visibly so you can watch
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            for index, prod in enumerate(products, 1):
                category = prod["category"]
                sku = prod["sku"]
                query = prod["query"]
                platforms = prod["platforms"]

                print(f"\n{'='*60}")
                print(f"[{index}/{len(products)}] Category: {category} | SKU: {sku}")
                print(f"  Query: {query}")
                print(f"  Platforms: {', '.join(platforms)}")
                print(f"{'='*60}")

                all_results = []

                if "amazon" in platforms:
                    amazon_results = scrape_amazon_playwright(page, query, sku, category, top_n=3)
                    all_results.extend(amazon_results)
                    time.sleep(1)

                if "flipkart" in platforms:
                    flipkart_results = scrape_flipkart_playwright(page, query, sku, category, top_n=3)
                    all_results.extend(flipkart_results)
                    time.sleep(1)

                safe_category = category.replace(" / ", "_").replace(" ", "_")
                output_filename = f"{safe_category}_{sku}.csv"
                save_to_csv(all_results, output_filename)

        finally:
            print("\n" + "=" * 70)
            print("Playwright scraping complete! Closing browser...")
            browser.close()
            print(f"All Playwright results & screenshots saved in:")
            print(f"  {OUTPUT_DIR}")
            print("=" * 70)

if __name__ == "__main__":
    main()
