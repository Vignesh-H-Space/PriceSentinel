import os
import csv
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
# 3. INITIALIZE SELENIUM CHROME BROWSER (VISIBLE)
# ==============================================================================
def create_browser():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Stealth tweak
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    return driver

# ==============================================================================
# 4. AMAZON SCRAPER (FILTER ADS + SCROLL TO REAL PRODUCTS)
# ==============================================================================
def scrape_amazon_visual(driver, query, sku, category, top_n=3):
    print(f"    [Amazon] Navigating to amazon.in...")
    driver.get("https://www.amazon.in")
    time.sleep(2)

    results = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_cat = category.replace(" / ", "_").replace(" ", "_")
    screenshot_name = f"{safe_cat}_{sku}_amazon.png"
    screenshot_path = os.path.join(OUTPUT_DIR, screenshot_name)

    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
        )
        search_box.clear()
        for char in query:
            search_box.send_keys(char)
            time.sleep(0.02)
        search_box.send_keys(Keys.RETURN)

        print(f"    [Amazon] Waiting for search results...")
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
        )

        # Scroll down slightly to skip top video/banner ad and bring actual products into view
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)

        # Save screenshot showing the actual product listings
        driver.save_screenshot(screenshot_path)
        print(f"    [Amazon] Screenshot captured: {screenshot_name}")

        # Find product result cards
        all_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")

        for card in all_cards:
            if len(results) >= top_n:
                break

            title = None
            price = None
            link = None

            # 1. Title
            title_elems = card.find_elements(By.CSS_SELECTOR, "h2 a span") or \
                          card.find_elements(By.CSS_SELECTOR, "h2 span")
            if title_elems:
                title = title_elems[0].text.strip()

            # 2. Link
            link_elems = card.find_elements(By.CSS_SELECTOR, "h2 a")
            if link_elems:
                link = link_elems[0].get_attribute("href")

            # 3. Price
            price_elems = card.find_elements(By.CSS_SELECTOR, ".a-price .a-offscreen") or \
                          card.find_elements(By.CSS_SELECTOR, ".a-price-whole")
            if price_elems:
                raw_price = price_elems[0].get_attribute("textContent") or price_elems[0].text
                raw_price = raw_price.replace("₹", "").replace(",", "").replace(".", "").strip()
                try:
                    price = float(raw_price)
                except ValueError:
                    price = None

            # Filter out irrelevant accessories (price > 100)
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
        print(f"    [Amazon Warning/Error]: {e}")
        driver.save_screenshot(screenshot_path)

    print(f"    [Amazon] Successfully extracted {len(results)} valid product listings.")
    return results

# ==============================================================================
# 5. FLIPKART SCRAPER (MODERN SELECTORS + POPUP HANDLING)
# ==============================================================================
def scrape_flipkart_visual(driver, query, sku, category, top_n=3):
    print(f"    [Flipkart] Navigating to flipkart.com...")
    driver.get("https://www.flipkart.com")
    time.sleep(2)

    results = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_cat = category.replace(" / ", "_").replace(" ", "_")
    screenshot_name = f"{safe_cat}_{sku}_flipkart.png"
    screenshot_path = os.path.join(OUTPUT_DIR, screenshot_name)

    try:
        # Dismiss login popup if present
        try:
            close_btn = driver.find_elements(By.CSS_SELECTOR, "span._30XB9F, button._2KpZ6l._2doB4z")
            if close_btn:
                close_btn[0].click()
                time.sleep(1)
        except Exception:
            pass

        # Search bar
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='q'], input[title*='Search']"))
        )
        search_box.clear()
        for char in query:
            search_box.send_keys(char)
            time.sleep(0.02)
        search_box.send_keys(Keys.RETURN)

        # Wait for either product cards or price symbols to appear
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(), '₹')]")) > 0
            )
        except Exception:
            pass

        # Scroll down so product cards render their images and text
        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(2)

        driver.save_screenshot(screenshot_path)
        print(f"    [Flipkart] Screenshot captured: {screenshot_name}")

        # Ultra-resilient: Find cards containing price symbol
        cards = driver.find_elements(By.XPATH, "//div[@data-id and .//*[contains(text(), '₹')]]")
        if not cards:
            cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') and .//*[contains(text(), '₹')]]")
        if not cards:
            cards = driver.find_elements(By.CSS_SELECTOR, "div.tUxRFH, div._75nlfW, div.slAVV4, div.cPHDOP")

        for card in cards:
            if len(results) >= top_n:
                break

            title = None
            price = None
            link = None

            # 1. Price: Find any text containing '₹' inside the card
            p_elems = card.find_elements(By.XPATH, ".//*[contains(text(), '₹')]")
            if p_elems:
                for pe in p_elems:
                    raw_txt = (pe.get_attribute("textContent") or pe.text).strip()
                    # Look for pattern like ₹53,990 or ₹1,250
                    if "₹" in raw_txt:
                        clean_num = raw_txt.split("₹")[-1].split()[0].replace(",", "").strip()
                        try:
                            val = float(clean_num)
                            if val > 50:  # avoid discount tags like '₹50 off'
                                price = val
                                break
                        except ValueError:
                            continue

            # 2. Title: Look for title divs, anchors, or image alt tags
            t_elems = card.find_elements(By.XPATH, ".//div[contains(@class, 'KzDlHZ') or contains(@class, '_4rR01T')]") or \
                      card.find_elements(By.XPATH, ".//a[contains(@class, 'wjcEIp') or contains(@class, 's1Q9rs') or contains(@class, 'WKTcLC')]") or \
                      card.find_elements(By.XPATH, ".//a[contains(@href, '/p/')]")
            if t_elems:
                for te in t_elems:
                    t_text = (te.get_attribute("textContent") or te.text).strip()
                    if len(t_text) > 10 and "₹" not in t_text:
                        title = t_text
                        break

            # If title is still missing, check image alt attribute
            if not title:
                img_elems = card.find_elements(By.XPATH, ".//img[@alt]")
                if img_elems:
                    alt = img_elems[0].get_attribute("alt")
                    if alt and len(alt) > 5:
                        title = alt.strip()

            # 3. Link
            l_elems = card.find_elements(By.XPATH, ".//a[contains(@href, '/p/')]") or \
                      card.find_elements(By.XPATH, ".//a[@href]")
            if l_elems:
                raw_link = l_elems[0].get_attribute("href")
                if raw_link:
                    link = raw_link if raw_link.startswith("http") else "https://www.flipkart.com" + raw_link

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
        print(f"    [Flipkart Warning/Error]: {e}")
        driver.save_screenshot(screenshot_path)

    print(f"    [Flipkart] Successfully extracted {len(results)} valid product listings.")
    return results

# ==============================================================================
# 6. CSV SAVER
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
    print(f"  --> Saved {len(records)} rows to: {filename}")

# ==============================================================================
# 7. MAIN ORCHESTRATION
# ==============================================================================
def main():
    print("=" * 70)
    print("  VISUAL PRICE SCRAPER (Selenium + Real Browser)")
    print("  Reading products from: scraping_input.csv")
    print("=" * 70)

    products = load_input_products(INPUT_FILE)
    print(f"\nLoaded {len(products)} products to scrape.\n")

    driver = create_browser()

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
                amazon_results = scrape_amazon_visual(driver, query, sku, category, top_n=3)
                all_results.extend(amazon_results)
                time.sleep(1.5)

            if "flipkart" in platforms:
                flipkart_results = scrape_flipkart_visual(driver, query, sku, category, top_n=3)
                all_results.extend(flipkart_results)
                time.sleep(1.5)

            safe_category = category.replace(" / ", "_").replace(" ", "_")
            output_filename = f"{safe_category}_{sku}.csv"
            save_to_csv(all_results, output_filename)

    finally:
        print("\n" + "=" * 70)
        print("Scraping run complete! Closing browser...")
        driver.quit()
        print(f"All results & screenshots are inside:")
        print(f"  {OUTPUT_DIR}")
        print("=" * 70)

if __name__ == "__main__":
    main()
