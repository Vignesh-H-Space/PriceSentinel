# Install the following Packages
# pip install selenium webdriver-manager

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
    """
    Reads the scraping_input.csv file.
    Each row has: category, sku, query, platforms (semicolon-separated)
    Returns a list of dictionaries.
    """
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
    """
    Opens a real, visible Chrome browser window.
    webdriver_manager automatically downloads the correct ChromeDriver.
    """
    chrome_options = Options()
    # Keep browser visible (no headless mode) so user can watch
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    # Reduce bot detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Stealth tweak: remove the "Chrome is being controlled by automated software" bar
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    return driver

# ==============================================================================
# 4. AMAZON SCRAPER (VISUAL WITH SCREENSHOTS)
# ==============================================================================
def scrape_amazon_visual(driver, query, sku, category, top_n=3):
    """
    1. Opens amazon.in
    2. Types query into search bar (visible keystrokes)
    3. Presses Enter
    4. Waits for results to load
    5. Takes a screenshot
    6. Extracts top_n product listings
    """
    print(f"    [Amazon] Opening amazon.in...")
    driver.get("https://www.amazon.in")
    time.sleep(2)

    results = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    screenshot_name = f"{category.replace(' / ', '_').replace(' ', '_')}_{sku}_amazon.png"
    screenshot_path = os.path.join(OUTPUT_DIR, screenshot_name)

    try:
        # Find the search box and type the query
        print(f"    [Amazon] Searching: {query}...")
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
        )
        search_box.clear()
        # Type character by character for visible effect
        for char in query:
            search_box.send_keys(char)
            time.sleep(0.03)
        time.sleep(0.5)
        search_box.send_keys(Keys.RETURN)

        # Wait for search results to load
        print(f"    [Amazon] Waiting for results...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
        )
        time.sleep(2)

        # Take screenshot of the search results page
        driver.save_screenshot(screenshot_path)
        print(f"    [Amazon] Screenshot saved: {screenshot_name}")

        # Extract top_n product cards
        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")

        for card in cards[:top_n]:
            try:
                # Title
                title_elem = card.find_element(By.CSS_SELECTOR, "h2 a span")
                title = title_elem.text.strip() if title_elem else "N/A"

                # Link
                link_elem = card.find_element(By.CSS_SELECTOR, "h2 a")
                link = link_elem.get_attribute("href") if link_elem else "N/A"

                # Price
                try:
                    price_elem = card.find_element(By.CSS_SELECTOR, ".a-price-whole")
                    price_str = price_elem.text.strip().replace(",", "").replace(".", "")
                    price = float(price_str)
                except Exception:
                    price = None

                if title and price:
                    results.append({
                        "Seller_name": "Amazon Seller",
                        "SKU": sku,
                        "Category": category,
                        "Region": "IN",
                        "Advertised_price": price,
                        "Marketplace": "Amazon",
                        "Screenshot": screenshot_name,
                        "Live_link": link,
                        "Last_time_collected": collected_at,
                        "Product_Title": title
                    })
            except Exception:
                continue

    except Exception as e:
        print(f"    [Amazon Error] {e}")
        driver.save_screenshot(screenshot_path)

    print(f"    [Amazon] Extracted {len(results)} listings.")
    return results

# ==============================================================================
# 5. FLIPKART SCRAPER (VISUAL WITH SCREENSHOTS)
# ==============================================================================
def scrape_flipkart_visual(driver, query, sku, category, top_n=3):
    """
    1. Opens flipkart.com
    2. Closes login popup if it appears
    3. Types query into search bar (visible keystrokes)
    4. Presses Enter
    5. Waits for results to load
    6. Takes a screenshot
    7. Extracts top_n product listings
    """
    print(f"    [Flipkart] Opening flipkart.com...")
    driver.get("https://www.flipkart.com")
    time.sleep(2)

    results = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    screenshot_name = f"{category.replace(' / ', '_').replace(' ', '_')}_{sku}_flipkart.png"
    screenshot_path = os.path.join(OUTPUT_DIR, screenshot_name)

    try:
        # Flipkart often shows a login popup — close it
        try:
            close_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button._2KpZ6l._2doB4z"))
            )
            close_btn.click()
            print(f"    [Flipkart] Closed login popup.")
            time.sleep(1)
        except Exception:
            pass  # No popup appeared, continue

        # Find search box and type the query
        print(f"    [Flipkart] Searching: {query}...")
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[title='Search for Products, Brands and More']"))
        )
        search_box.clear()
        for char in query:
            search_box.send_keys(char)
            time.sleep(0.03)
        time.sleep(0.5)
        search_box.send_keys(Keys.RETURN)

        # Wait for results
        print(f"    [Flipkart] Waiting for results...")
        time.sleep(4)

        # Take screenshot
        driver.save_screenshot(screenshot_path)
        print(f"    [Flipkart] Screenshot saved: {screenshot_name}")

        # Extract product cards (Flipkart changes its CSS classes frequently)
        # Try multiple known selectors
        cards = driver.find_elements(By.CSS_SELECTOR, "div._1AtVbE div._13oc-S")
        if not cards:
            cards = driver.find_elements(By.CSS_SELECTOR, "div.cPHDOP")
        if not cards:
            cards = driver.find_elements(By.CSS_SELECTOR, "div._75nlfW")
        if not cards:
            cards = driver.find_elements(By.CSS_SELECTOR, "div.slAVV4")

        for card in cards[:top_n]:
            try:
                # Title
                title_elem = (
                    card.find_elements(By.CSS_SELECTOR, "div._4rR01T") or
                    card.find_elements(By.CSS_SELECTOR, "a.s1Q9rs") or
                    card.find_elements(By.CSS_SELECTOR, "a.wjcEIp") or
                    card.find_elements(By.CSS_SELECTOR, "a.WKTcLC")
                )
                title = title_elem[0].text.strip() if title_elem else "N/A"

                # Price
                price_elem = (
                    card.find_elements(By.CSS_SELECTOR, "div._30jeq3") or
                    card.find_elements(By.CSS_SELECTOR, "div.Nx9bqj")
                )
                if price_elem:
                    price_str = price_elem[0].text.strip().replace("₹", "").replace(",", "")
                    price = float(price_str)
                else:
                    price = None

                # Link
                link_elem = (
                    card.find_elements(By.CSS_SELECTOR, "a._1fQZEK") or
                    card.find_elements(By.CSS_SELECTOR, "a.s1Q9rs") or
                    card.find_elements(By.CSS_SELECTOR, "a.VJA3rP") or
                    card.find_elements(By.CSS_SELECTOR, "a.wjcEIp") or
                    card.find_elements(By.CSS_SELECTOR, "a.WKTcLC")
                )
                link = "https://www.flipkart.com" + link_elem[0].get_attribute("href") if link_elem else "N/A"
                # Fix double domain if href already contains full URL
                if link_elem and link_elem[0].get_attribute("href").startswith("http"):
                    link = link_elem[0].get_attribute("href")

                if title != "N/A" and price:
                    results.append({
                        "Seller_name": "Flipkart Seller",
                        "SKU": sku,
                        "Category": category,
                        "Region": "IN",
                        "Advertised_price": price,
                        "Marketplace": "Flipkart",
                        "Screenshot": screenshot_name,
                        "Live_link": link,
                        "Last_time_collected": collected_at,
                        "Product_Title": title
                    })
            except Exception:
                continue

    except Exception as e:
        print(f"    [Flipkart Error] {e}")
        driver.save_screenshot(screenshot_path)

    print(f"    [Flipkart] Extracted {len(results)} listings.")
    return results

# ==============================================================================
# 6. SAVE RESULTS TO INDIVIDUAL CSV FILE
# ==============================================================================
def save_to_csv(records, filename):
    """Writes scraped records to a CSV file in the visual_results folder."""
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
    print("  VISUAL PRICE SCRAPER (Selenium + Chrome)")
    print("  Reading products from: scraping_input.csv")
    print("=" * 70)

    # Load products from the dynamic input file
    products = load_input_products(INPUT_FILE)
    print(f"\nLoaded {len(products)} products to scrape.\n")

    # Launch the visible Chrome browser
    print("Launching Chrome browser...")
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

            # Scrape each requested platform
            if "amazon" in platforms:
                amazon_results = scrape_amazon_visual(driver, query, sku, category, top_n=3)
                all_results.extend(amazon_results)
                time.sleep(2)

            if "flipkart" in platforms:
                flipkart_results = scrape_flipkart_visual(driver, query, sku, category, top_n=3)
                all_results.extend(flipkart_results)
                time.sleep(2)

            # Save this product's results to its own CSV file
            safe_category = category.replace(" / ", "_").replace(" ", "_")
            output_filename = f"{safe_category}_{sku}.csv"
            save_to_csv(all_results, output_filename)

    finally:
        print("\n" + "=" * 70)
        print("Scraping complete! Closing browser...")
        driver.quit()
        print(f"All results and screenshots saved in:")
        print(f"  {OUTPUT_DIR}")
        print("=" * 70)

if __name__ == "__main__":
    main()
