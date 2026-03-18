import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "vishal_sales")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

# Load and seed products
json_files = [
    ("../../flipkart_products.json", "general"),
    ("../frontend/laptop.json", "laptop"),
    ("../frontend/mobile.json", "mobile"),
    ("../frontend/mobile_accessories.json", "accessories"),
]

print("Starting database seeding...")

for filepath, category in json_files:
    abs_path = os.path.join(os.path.dirname(__file__), filepath)
    if os.path.exists(abs_path):
        try:
            with open(abs_path, encoding='utf-8') as f:
                data = json.load(f)
            products = data if isinstance(data, list) else data.get("products", [])
            
            for p in products:
                if "category" not in p or not p["category"]:
                    p["category"] = category
                
                # Ensure required fields exist
                if "name" not in p and "title" in p:
                    p["name"] = p["title"]
                if "price" not in p and "discountprice" in p:
                    p["price"] = p["discountprice"]
                
                # Update or insert
                filter_query = {}
                if "name" in p and p["name"]:
                    filter_query["name"] = p["name"]
                if "brand" in p and p["brand"]:
                    filter_query["brand"] = p["brand"]
                
                if filter_query:
                    db.products.update_one(filter_query, {"$set": p}, upsert=True)
                else:
                    db.products.insert_one(p)
            
            print(f"✅ Seeded {len(products)} products from {filepath}")
        except Exception as e:
            print(f"❌ Failed to seed {filepath}: {e}")
    else:
        print(f"⚠️  File not found: {abs_path}")

print("🎉 Database seeding complete!")
print(f"Total products in database: {db.products.count_documents({})}")
