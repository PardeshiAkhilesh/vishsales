import os
import json
import uuid
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


class FlipkartMobileScraper:
    def __init__(self, delay=2):
        self.delay = delay
        self.start_url = "https://www.flipkart.com/search?q=mobile&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off&page={}"
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=chrome_options)

    def extract_offers(self, psoup):
        offers_list = []
        offer_items = psoup.find_all("li", {"class": "kF1Ml8 col"})
        for item in offer_items:
            spans = item.find_all("span")
            if len(spans) >= 2:
                label = spans[0].get_text(strip=True)
                offer_text = spans[1].get_text(strip=True)
                full_offer = f"{label}: {offer_text}"
                offers_list.append(full_offer)
        return offers_list




    def extract_image_url(self, psoup):
        try:
            image_urls = []
            image_div = psoup.find("div", class_="_0J1TKd")
            if image_div:
                img_tags = image_div.find_all("img", class_="_0DkuPH")
                for img in img_tags:
                    src = img.get("src")
                    if src and src not in image_urls:
                        image_urls.append(src)

            thumbnail = image_urls[0] if image_urls else ""
            return {
                "thumbnail": thumbnail,
                "urls": image_urls
            }
        except Exception:
            return {
                "thumbnail": "",
                "urls": []
            }


    def extract_mobile_features(self, psoup):
        features = {
            "type": "mobile",
            "details": {
                "storage": {"ram": "", "rom": ""},
                "design": {
                    "dimensions": "", "weight": "", "form_factor": "",
                    "stylus_support": "", "color": ""
                },
                "display": {
                    "screen_size": "", "screen_resolution": "",
                    "touchscreen": "", "display_features": ""
                },
                "performance": {
                    "processor": "", "cores": "", "gpu": "",
                    "operating_system": "", "model_number": ""
                },
                "network&connectivity": {
                    "wireless_tech": "", "connectivity": "", "gps": "",
                    "sim": "", "mobile_hotspot": ""
                },
                "camera": {
                    "rear_camera": "", "front_camera": "",
                    "camera_features": ""
                },
                "battery": {
                    "battery_capacity": "", "battery_type": "", "fast_charging": ""
                },
                "audio": {"audio_jack": ""},
                "box_contents": {"in_the_box": ""},
                "manufacturer": {"brand": ""}
            }
        }

        spec_section = psoup.find("div", class_="_3Fm-hO")
        if spec_section:
            rows = spec_section.find_all("tr", class_="WJdYP6 row")
            raw_specs = {}
            for row in rows:
                label_td = row.find("td", class_="+fFi1w col col-3-12")
                value_td = row.find("td", class_="Izz52n col col-9-12")
                if label_td and value_td:
                    label = label_td.get_text(strip=True).upper()
                    value_list = value_td.find_all("li", class_="HPETK2")
                    value = ', '.join(li.get_text(strip=True) for li in value_list)
                    raw_specs[label] = value

            features["details"]["storage"]["ram"] = raw_specs.get("RAM", "")
            features["details"]["storage"]["rom"] = raw_specs.get("INTERNAL STORAGE", "")
            features["details"]["manufacturer"]["brand"] = raw_specs.get("BRAND", "")
            features["details"]["display"]["screen _resolution"] = raw_specs.get("RESOLUTION", "")
            features["details"]["battery"]["battery_capacity"] = raw_specs.get("BATTERY CAPACITY", "")
            features["details"]["battery"]["battery_Type"] = raw_specs.get("BATTERY TYPE","")
            features["details"]["display"]["touchscreen"] = raw_specs.get("TOUCHSCREEN","")
            features["details"]["design"]["color"] = raw_specs.get("COLOR", "")
            features["details"]["display"]["display_features"] = raw_specs.get("OTHER DISPLAY FEATURE", "")
            # Join separate dimensions (Width x Height x Depth)
            width = raw_specs.get("WIDTH", "")
            height = raw_specs.get("HEIGHT", "")
            depth = raw_specs.get("DEPTH", "")

            dimensions = ""
            if width or height or depth:
                dimensions = f"{width} x {height} x {depth}".strip(" x")

            features["details"]["Design"]["Dimensions"] = dimensions

            features["details"]["design"]["weight"] = raw_specs.get("WEIGHT", "")
            features["details"]["performance"]["processor"] = raw_specs.get("PROCESSOR BRAND", "")
            features["details"]["network&connectivity"]["sim"] = raw_specs.get("SIM TYPE", "")
            Internet_connectivity = raw_specs.get("INTERNET CONNECTIVITY","")
            Bluetooth = raw_specs.get("BLUETOOTH SUPPORT","")
            B_version = raw_specs.get("BLUETOOTH VERSION","")
            Connectivity = ""
            if Internet_connectivity or Bluetooth or B_version:
                Connectivity = f"{Internet_connectivity} x {Bluetooth} x {B_version}".strip("x")
            features["details"]["network&connectivity"] = Connectivity
            features["details"]["performance"]["operating_system"] = raw_specs.get("OPERATING SYSTEM", "")
            features["details"]["performance"]["model_number"] = raw_specs.get("MODEL NUMBER", "")
            features["details"]["battery"]["fast_charging"] = raw_specs.get("QUICK CHARGING", "")
            features["details"]["camera"]["rear_camera"] = raw_specs.get("FLASH", "")
            features["details"]["camera"]["front_camera"] = raw_specs.get("SECONDARY CAMERA FEATURE", "")
            features["details"]["camera"]["camera_features"] = raw_specs.get("PRIMARY CAMERA FEATURE", "")
            features["details"]["audio"]["audio_jack"] = raw_specs.get("AUDIO FORMATS", "")
            features["details"]["design"]["form_factor"] = raw_specs.get("FORM FACTOR", "")
            features["details"]["box_contents"]["in_the_box"] = raw_specs.get("IN THE BOX", "")

        return features

    def scrape(self):
        all_data = []

        for page in range(1, 3):
            print(f"Scraping Page {page}")
            self.driver.get(self.start_url.format(page))
            time.sleep(self.delay)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            links = soup.find_all("a", class_="CGtC98")
            product_links = ["https://www.flipkart.com" + link.get("href") for link in links if link.get("href")]

            for url in product_links:
                try:
                    self.driver.get(url)
                    time.sleep(self.delay)
                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                    title_tag = psoup.find("span", class_="VU-ZEz")
                    product_name = title_tag.get_text(strip=True) if title_tag else ""

                    title = product_name  # This is the title to use in JSON output
                    actual_price_tag=psoup.find("div",class_="yRaY8j A6+E6v")
                    actual_price=actual_price_tag.get_text(strip=True).replace("₹", "").replace(",", "") if actual_price_tag else ""
                    print("actualprice>>",actual_price)


                    price_tag = psoup.find("div", class_="Nx9bqj CxhGGd")
                    price = price_tag.get_text(strip=True).replace("₹", "").replace(",", "") if price_tag else ""

                    rating_tag = psoup.find("div", class_="XQDdHH")
                    rating = rating_tag.get_text(strip=True) if rating_tag else ""

                    brand = product_name.split()[0] if product_name else ""
                    category = "smartphone"

                    data = {
                        "product_id": str(uuid.uuid4()),
                        "title": title,
                        "price":actual_price,
                        "discounted_price": price,
                        "rating": rating,
                        "brand": brand,
                        "offers": self.extract_offers(psoup),
                         "image": self.extract_image_url(psoup),
                        "features": self.extract_mobile_features(psoup),
                        "category": category,
                        "affilatelink": url
                    }

                    all_data.append(data)
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    continue

        self.driver.quit()

        # Save to JSON
        # os.makedirs("database", exist_ok=True)
        with open("flipkart_mobile_new.json", "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print("Data saved to flipkart_mobile_new.json")


if __name__ == "__main__":
    scraper = FlipkartMobileScraper()
    scraper.scrape()