from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import pandas as pd
import time
import random
import re
import json
import uuid


class AmazonMobileScraper:
    def __init__(self, delay=3):
        self.delay = delay
        self.user_agents = [
            
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36",
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.57 Safari/537.36"

            
        ]
        options = Options()
        
        options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def close(self):
        self.driver.quit()

    def scrape_mobiles(self, search_term="realme mobile", max_pages=1):
        all_data = []
        for page in range(1, max_pages + 1):
            query = quote_plus(search_term)
            url = f"https://www.amazon.in/s?k={query}&page={page}"
            self.driver.get(url)
            self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@data-component-type='s-search-result']")))
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            cards = soup.find_all("div", {"data-component-type": "s-search-result"})

            for card in cards:
                try:
                    link_tag = card.find("a", href=True)
                    if not link_tag:
                        continue

                    raw_href = link_tag["href"]
                    match = re.search(r"(/dp/[A-Z0-9]{10})", raw_href)
                    product_url = f"https://www.amazon.in{match.group(1)}" if match else None
                    print(f"Scraping product URL: {product_url}")
                    if product_url:
                        self.driver.get(product_url)
                    else:
                        print(f"⚠ Skipping invalid URL")
                        continue

                    # if product_url != "N/A" and product_url.startswith("http"):
                    #     self.driver.get(product_url)
                    #     # continue scraping
                    # else:
                    #     print(f"⚠ Skipping invalid URL: {product_url}")
                    #     continue


                    # self.driver.get(product_url)
                    self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")
                    product_id = str(uuid.uuid4())
                    title_tag = psoup.find("span", id="productTitle")
                    raw_title = title_tag.get_text(strip=True).replace("|","") if title_tag else "N/A"
                    print(f"Raw title found: {raw_title}")
                    product_name = " ".join(raw_title.split()[0:3])
                    print(f"Product name extracted: {product_name}")
                    Brand = product_name.split()[0] if product_name else "N/A"
            
                    whole = psoup.find("span", class_="a-price-whole")
                    fraction = psoup.find("span", class_="a-price-fraction")
                    if whole:


                        whole_price = whole.get_text(strip=True).replace(',', '').replace('.', '')
                        if fraction:
                         
                         fraction_price = fraction.get_text(strip=True)
                         price = f"₹{whole_price}.{fraction_price}"
                        else:
                         
                         price = f"₹{whole_price}.00"
                    else:
                        price = "N/A"

                    actual_price_tag = psoup.find("span", class_="a-price a-text-price")
                    actual_price = "N/A"
                    if actual_price_tag:
                        offscreen_span = actual_price_tag.find("span", class_="a-offscreen")
                        if offscreen_span:
                            actual_price = offscreen_span.get_text(strip=True)

                            
                    offers = []
                    offer_section = psoup.find("div", class_="a-cardui vsx__offers-holder")

                    if offer_section:
                        for block in offer_section.find_all("div", recursive=True):
                            # Try to find known text structure
                            title_elem = block.find("h6", class_="a-size-base a-spacing-micro offers-items-title")
                            value_elem = block.find("span", class_="a-truncate-full a-offscreen")

                            if title_elem and value_elem:
                                combined = f"{title_elem.get_text(strip=True)}: {value_elem.get_text(strip=True)}"
                                if combined not in offers:
                                    offers.append(combined)
                            else:
                                # Fallback to extracting raw text if key-value not available
                                text = block.get_text(strip=True)
                                if text and text not in offers:
                                    offers.append(text)
                    else:
                        offers = ["No offers listed"]  
                    print("OFFERS",offers)          

                   
                    
                    rating_tag = psoup.select_one("#acrPopover > span.a-declarative > a > span")
                    rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"
                    # Extract main thumbnail image
                    image_urls = set()

                    image_wrappers = psoup.find_all("div", class_="imgTagWrapper")
                    for wrapper in image_wrappers:
                        img_tag = wrapper.find("img")
                        if img_tag and img_tag.has_attr("src"):
                            image_urls.add(img_tag["src"])
                    thumbnail_items = psoup.find_all("li", class_="a-spacing-small item imageThumbnail a-declarative")
                    for item in thumbnail_items:
                        span = item.find("span", class_="a-button-text")
                        if span:
                            # Check for data-a-dynamic-image
                            data_dynamic = span.get("data-a-dynamic-image")
                            if data_dynamic:
                                try:
                                    images_dict = json.loads(data_dynamic)
                                    # Get the largest version (based on width)
                                    sorted_imgs = sorted(images_dict.items(), key=lambda x: x[1][0], reverse=True)
                                    for img_url, _ in sorted_imgs:
                                        image_urls.add(img_url)
                                except json.JSONDecodeError:
                                    pass
                            else:
                                # fallback to <img> tag
                                img = span.find("img")
                                if img and img.has_attr("src"):
                                    image_urls.add(img["src"])
                                # fallback to style="background-image"
                                style = span.get("style", "")
                                match = re.search(r"url\(['\"]?(https.*?\.jpg)['\"]?\)", style)
                                if match:
                                    image_urls.add(match.group(1))

                    # 3. Final output
                    image_urls = list(image_urls)
                    image_data = {
                        "thumbnail": image_urls[0] if image_urls else "N/A",
                        "urls": image_urls
                    }

                    print(image_data)
                                        
                    raw_specs_table = psoup.find("table", class_="a-keyvalue prodDetTable")
                    raw_specs = {}
                    
                    if raw_specs_table:
                        rows = raw_specs_table.find_all("tr")
                        for row in rows:
                            th = row.find("th")
                            td = row.find("td")
                            if th and td:
                                key = th.get_text(strip=True)
                                value = td.get_text(strip=True)
                                raw_specs[key] = value
                        print("raw.............",raw_specs)        

                    features = {
                        "type": "mobile",
                        "details": {
                            "Design": {
                                "dimensions": "",
                                "weight": "",
                                "form_factor": "",
                                "stylus_support": "",
                                "color": ""
                            },
                            "display": {
                                "resolution": "",
                                "touch_screen": "",
                                "Display Features": ""
                            },
                            "Network & Connectivity": {
                                "Wireless Tech": "",
                                "Connectivity": "",
                                "GPS": "",
                                "SIM": "",
                                "Mobile Hotspot": ""
                            },
                            "Performance": {
                                "Operating System": "",
                                "Model Number": "",
                                "processor":" "
                            },
                            "storage":{"ram":" ",
                                       
                                       "rom":" "
                            },
                            "Camera": {

                            "Rear Camera":"",
                            "Front Camera":"",
                            "Camera Features": ""
                              },
                            "Battery": {
                                "Battery Capacity": "",
                                "Battery Type": "",
                                "Fast Charging": ""
                            },
            
                            "Audio": {
                                "Audio Jack": ""
                            },
                            "Box Contents": {
                                "In the Box": ""
                            },
                            "Manufacturer": {
                                "Brand": ""
                            }
                        }
                    }
                    storage = psoup.find("table", class_="a-normal a-spacing-micro") 
                    if storage:
                        ramandrom = storage.find_all('tr')
                        for i in ramandrom:
                            column = i.find_all("td")
                            if len(column) >= 2:
                                key1 = column[0].get_text(strip=True).lower()
                                print(">>>>>>>>>>",key1)
                                value1 = column[1].get_text(strip=True).lower()
                                print("value1>>>>",value1)
                                if "ram" in key1:
                                    features['details']["storage"]["ram"] = value1
                                elif "internal storage" in key1 or "rom" in key1 or "memory storage capacity" in key1 or "storage" in key1:
                                  features['details']["storage"]["rom"] = value1
                                elif "cpu model" in key1 or "processor"in key1:
                                    
                                     features["details"]["Performance"]["processor"]=value1
                                                    
                    if "Product Dimensions" in raw_specs:
                        parts = raw_specs["Product Dimensions"].split(";")
                        if len(parts) >= 2:
                            features["details"]["Design"]["Dimensions"] = parts[0].strip()
                            features["details"]["Design"]["Weight"] = parts[1].strip()
                          
                    if "Item Weight" in raw_specs and not features["details"]["Design"].get("Weight"):
                        features["details"]["Design"]["Weight"] = raw_specs["Item Weight"]
                    features["details"]["Performance"]["Operating System"] = raw_specs.get("OS", "")
                    features["details"]["Performance"]["Model Number"] = raw_specs.get("Item model number", "")
                    features["details"]["Performance"]["processor"]=raw_specs.get("Processor"," ")
                    features["details"]["Camera"]["Rear Camera"] = raw_specs.get("REAR CAMERA", "")
                    features["details"]["Camera"]["Front Camera"] = raw_specs.get("FRONT CAMERA", "")
                    features["details"]["Camera"]["Camera Features"] = raw_specs.get("Other camera features", "")
                    features["details"]["Battery"]["Battery Capacity"] = raw_specs.get("Battery Power Rating", "").replace("Milliamp Hours", "mAh")
                    features["details"]["Battery"]["Battery Type"] = "Lithium Ion" if "Lithium Ion" in raw_specs.get("Batteries", "") else ""
                    features["details"]["Audio"]["Audio Jack"] = raw_specs.get("Audio Jack", "")
                    features["details"]["Manufacturer"]["Brand"] = raw_specs.get("Manufacturer", "")
                    features["details"]["Box Contents"]["In the Box"] = raw_specs.get("Whats in the box", "")
                    features["details"]["Display"]["Resolution"] = raw_specs.get("Resolution", "")
                    features["details"]["Display"]["Display Features"] = raw_specs.get("Other display features", "")
                    features["details"]["Display"]["Touch Screen"] = "Yes" if "Touchscreen" in raw_specs.get("Device interface - primary", "") else ""
                    features["details"]["Design"]["Stylus Support"] = "Yes" if "Stylus" in raw_specs.get("Device interface - primary", "") else ""
                    features["details"]["Design"]["Form Factor"] = raw_specs.get("Form factor", "")
                    features["details"]["Design"]["Color"] = raw_specs.get("Colour", "").capitalize()
                    features["details"]["Network & Connectivity"]["Wireless Tech"] = raw_specs.get("Wireless communication technologies", "")
                    features["details"]["Network & Connectivity"]["Connectivity"] = raw_specs.get("Connectivity technologies", "")
                    features["details"]["Network & Connectivity"]["GPS"] = raw_specs.get("GPS", "")
                   
                    special = raw_specs.get("Special features", "")
                    if "Dual SIM" in special:
                        features["details"]["Network & Connectivity"]["SIM"] = "Dual SIM"
                    if "Mobile Hotspot" in special:
                        features["details"]["Network & Connectivity"]["Mobile Hotspot"] = "Yes"
                    if "Fast Charging" in special:
                        features["details"]["Battery"]["Fast Charging"] = "Yes"
                    if "Always On Display" in special:
                        if features["details"]["Display"]["Display Features"]:
                            features["details"]["Display"]["Display Features"] += ", Always On Display"
                        else:
                            features["details"]["Display"]["Display Features"] = "Always On Display"
                    print("features>>>>",features)        


                    all_data.append({
                        "product_id": product_id,
                        "title": raw_title,
                        "product_name": product_name,
                        "brand":Brand,
                        "price": actual_price,
                        "discounted_Price": price,
                        "rating": rating,
                        "offers": offers,
                        "features":features,
                        "affiliatelink": product_url,
                        "image_url":image_data,
                        "category": "smartphone",
                        "Store":"Amazon"
                    })
                    print(f"✔ Scraped:{product_name}")
                    time.sleep(self.delay)

                except Exception as e:
                    print(f"⚠ Skipping a product due to error: {e}")
                    continue

        self.driver.quit()
        return all_data
    def save_to_json(self, amazon_data, filename="backend/app/database/amazon_mobilesamsung.json"):
        try:
            json_string = json.dumps(amazon_data, indent=4, ensure_ascii=False)
            json_string = json_string.replace('\\/', '/')  # Clean slashes

            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_string)

            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Failed to save JSON: {e}")

if __name__ == "__main__":
    scraper = AmazonMobileScraper()
    try:
        results = scraper.scrape_mobiles("samsung mobile ", max_pages=1)
        df = pd.DataFrame(results)
        df.to_json("backend/app/database/amazon_mobilesamsung.json", orient="records", indent=2 , force_ascii=False)
        print(df.head())
    finally:
        scraper.close()


