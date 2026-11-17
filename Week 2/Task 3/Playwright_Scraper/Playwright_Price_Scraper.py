import os
import csv
import time
import datetime
from playwright.sync_api import sync_playwright

# ==============================================================================
# 1. PATHS & DIRECTORIES
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "scraping_input.csv")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "scraped_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================================================================
# 2. READ THE DYNAMIC INPUT FILE
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
# 3. PLAYWRIGHT AMAZON SCRAPER
# ==============================================================================
def scrape_amazon_playwright(page, query, sku, category, top_n=3):
    print(f"    [Playwright - Amazon] Navigating to amazon.in...")
    results = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_cat = category.replace(" / ", "_").replace(" ", "_")
    screenshot_name = f"{safe_cat}_{sku}_amazon.png"
    screenshot_path = os.path.join(OUTPUT_DIR, screenshot_name)

    try:
        # Navigate with a real desktop user-agent
        page.goto("https://www.amazon.in", wait_until="domcontentloaded", timeout=30000)
        time.sleep(1)

        # Type query in search bar (Playwright auto-waits for element)
        search_box = page.locator("#twotabsearchtextbox")
        search_box.fill("")
        search_box.type(query, delay=25)
        search_box.press("Enter")

        # Wait for product results to appear
        page.wait_for_selector("div[data-component-type='s-search-result']", timeout=15000)

        # Scroll down slightly to ensure lazy-loaded listings render
        page.mouse.wheel(0, 500)
        time.sleep(1.5)

        # Capture high-res screenshot
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
            title_elem = card.locator("h2 a span").first
            if title_elem.count() > 0:
                title = title_elem.inner_text().strip()

            # 2. Link
            link_elem = card.locator("h2 a").first
            if link_elem.count() > 0:
                href = link_elem.get_attribute("href")
                if href:
                    link = href if href.startswith("http") else "https://www.amazon.in" + href

            # 3. Price (check offscreen text or whole price)
            price_elem = card.locator(".a-price .a-offscreen").first
            if price_elem.count() > 0:
                raw_price = price_elem.inner_text().replace("₹", "").replace(",", "").replace(".", "").strip()
                try:
                    price = float(raw_price)
                except ValueError:
                    price = None

            # Filter out non-matching small accessories
            if title and price and price > 100:
                results.append({
                    "Seller_name": "Amazon Seller",
                    "SKU": sku,
                    "Category": category,
                    "Region": "IN",
                    "Advertised_price": price,
                    "Marketplace": "Amazon",
                    "Screenshot": screenshot_name,
                    "Live_link": link or "https://www.amazon.in",
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
# 4. PLAYWRIGHT FLIPKART SCRAPER
# ==============================================================================
def scrape_flipkart_playwright(page, query, sku, category, top_n=3):
    print(f"    [Playwright - Flipkart] Navigating to flipkart.com...")
    results = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_cat = category.replace(" / ", "_").replace(" ", "_")
    screenshot_name = f"{safe_cat}_{sku}_flipkart.png"
    screenshot_path = os.path.join(OUTPUT_DIR, screenshot_name)

    try:
        page.goto("https://www.flipkart.com", wait_until="domcontentloaded", timeout=30000)
        time.sleep(1)

        # Dismiss login popup if visible
        try:
            close_btn = page.locator("span._30XB9F, button._2KpZ6l._2doB4z").first
            if close_btn.is_visible():
                close_btn.click()
                time.sleep(0.5)
        except Exception:
            pass

        # Search bar
        search_box = page.locator("input[name='q'], input[title*='Search']").first
        search_box.fill("")
        search_box.type(query, delay=25)
        search_box.press("Enter")

        # Wait for price symbols to appear
        page.wait_for_selector("//*[contains(text(), '₹')]", timeout=15000)

        # Scroll down slightly so product cards render
        page.mouse.wheel(0, 400)
        time.sleep(1.5)

        page.screenshot(path=screenshot_path)
        print(f"    [Playwright - Flipkart] Screenshot captured: {screenshot_name}")

        # Locate product cards using our resilient XPath
        cards = page.locator("//div[@data-id and .//*[contains(text(), '₹')]]").all()
        if not cards:
            cards = page.locator("//a[contains(@href, '/p/') and .//*[contains(text(), '₹')]]").all()

        for card in cards:
            if len(results) >= top_n:
                break

            title = None
            price = None
            link = None

            # 1. Price
            p_elem = card.locator(".//*[contains(text(), '₹')]").first
            if p_elem.count() > 0:
                raw_txt = p_elem.inner_text().strip()
                if "₹" in raw_txt:
                    clean_num = raw_txt.split("₹")[-1].split()[0].replace(",", "").strip()
                    try:
                        val = float(clean_num)
                        if val > 50:
                            price = val
                    except ValueError:
                        price = None

            # 2. Title
            t_elem = card.locator(".//div[contains(@class, 'KzDlHZ') or contains(@class, '_4rR01T')]").first
            if t_elem.count() > 0:
                title = t_elem.inner_text().strip()
            else:
                # Fallback to link text or img alt
                link_t = card.locator(".//a[contains(@class, 'wjcEIp') or contains(@class, 's1Q9rs')]").first
                if link_t.count() > 0:
                    title = link_t.inner_text().strip()
                else:
                    img_elem = card.locator(".//img[@alt]").first
                    if img_elem.count() > 0:
                        alt = img_elem.get_attribute("alt")
                        if alt and len(alt) > 5:
                            title = alt.strip()

            # 3. Link
            l_elem = card.locator(".//a[contains(@href, '/p/')]").first
            if l_elem.count() > 0:
                href = l_elem.get_attribute("href")
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
                    "Live_link": link or "https://www.flipkart.com",
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
    print("  PLAYWRIGHT PRICE SCRAPER (Modern Chromium Engine)")
    print(f"  Reading products from: {INPUT_FILE}")
    print(f"  Saving results in:     {OUTPUT_DIR}")
    print("=" * 70)

    products = load_input_products(INPUT_FILE)
    print(f"\nLoaded {len(products)} products to scrape.\n")

    # Launch Playwright Chromium in visible mode (headless=False) so you can watch
    with sync_playwright() as p:
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
