import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from database.mongo import client as mongo_client
from bson import ObjectId

load_dotenv()

DB_NAME = os.getenv("MONGO_DB", "ecommerce")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ecommerce_data")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


FILTER_PROMPT = """You are a filter extractor for an electronics store. Extract search filters from the user's query.
Return ONLY a valid JSON object with these optional fields:
{
  "category": "smartphone" | "laptop" | "laptop accessories" | "mobile accessories" | null,
  "brand": "brand name or null",
  "min_price": number or null,
  "max_price": number or null,
  "ram": "e.g. 8GB or null",
  "storage": "e.g. 128GB or null",
  "processor": "e.g. snapdragon or null",
  "query": "short brand/model keyword for title search, or null. Do NOT put words like best/top/good/cheap/budget here",
  "sort_by": "rating" | "price_asc" | "price_desc" | null
}

Category mapping rules (strictly follow these):
- "mobile", "mobiles", "phone", "phones", "smartphone", "smartphones", "handset" -> "smartphone"
- "laptop", "laptops", "notebook", "notebooks" -> "laptop"
- "laptop accessory", "laptop accessories" -> "laptop accessories"
- "mobile accessory", "mobile accessories", "earphone", "charger", "cover", "case" -> "mobile accessories"

Sort rules:
- "best", "top", "recommended", "highest rated", "good" -> "rating"
- "cheapest", "lowest price", "budget", "affordable", "under X" -> "price_asc"
- "expensive", "premium", "highest price" -> "price_desc"

Do not include any explanation outside the JSON."""


CHAT_PROMPT = """You are a helpful electronics store assistant for Vishal Sales.
Answer the customer's question using the product data provided.
Give a detailed, friendly, textual response covering:
- Product name and brand
- Price (original and discounted if available)
- Key specifications: RAM, storage, display, camera, battery, processor
- Available offers and bank discounts
- Rating if available
- Any notable features

If multiple products are found, summarize the top options and highlight differences.
If no products are found, politely say so and suggest the customer refine their search.
Keep the response conversational and helpful. Do not use markdown tables."""


def convert_objectid(doc):
    if isinstance(doc, dict):
        return {k: convert_objectid(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [convert_objectid(i) for i in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    return doc


def extract_intent(user_message: str) -> dict:
    response = openai_client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
            {"role": "system", "content": FILTER_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0,
        max_tokens=200,
        timeout=10
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


def build_mongo_filter(intent: dict) -> dict:
    filters = {}

    CATEGORY_MAP = {
        "mobile": "smartphone", "mobiles": "smartphone", "phone": "smartphone",
        "phones": "smartphone", "handset": "smartphone", "smartphones": "smartphone",
        "laptop": "laptop", "laptops": "laptop", "notebook": "laptop", "notebooks": "laptop",
        "laptop accessories": "laptop accessories", "laptop accessory": "laptop accessories",
        "mobile accessories": "mobile accessories", "mobile accessory": "mobile accessories",
        "smartphone": "smartphone",
    }
    if intent.get("category"):
        raw_cat = intent["category"].lower().strip()
        filters["category"] = CATEGORY_MAP.get(raw_cat, raw_cat)

    if intent.get("brand"):
        filters["brand"] = {"$regex": intent["brand"], "$options": "i"}

    min_p = intent.get("min_price")
    max_p = intent.get("max_price")
    if min_p is not None or max_p is not None:
        expr_conds = []
        # Handle both discounted_price (Flipkart/JioMart) and discounted_Price (Amazon/Croma)
        def price_expr(field):
            return {"$toDouble": {"$replaceAll": {
                "input": {"$replaceAll": {"input": {"$toString": field}, "find": "₹", "replacement": ""}},
                "find": ",", "replacement": ""
            }}}
        p_lower = price_expr("$discounted_price")
        p_upper = price_expr("$discounted_Price")
        # Use whichever field is non-null/non-zero
        p_val = {"$cond": [{"$gt": [p_lower, 0]}, p_lower, p_upper]}
        if min_p is not None:
            expr_conds.append({"$gte": [p_val, float(min_p)]})
        if max_p is not None:
            expr_conds.append({"$lte": [p_val, float(max_p)]})
        filters["$expr"] = {"$and": expr_conds} if len(expr_conds) > 1 else expr_conds[0]

    def make_regex(value: str) -> dict:
        # Normalize "8GB" -> "8" so it matches "8 GB RAM", "8GB", "8 gb" etc.
        number = "".join(filter(str.isdigit, value))
        pattern = number if number else value
        return {"$regex": pattern, "$options": "i"}

    and_conditions = []

    if intent.get("ram"):
        ram_regex = make_regex(intent["ram"])
        and_conditions.append({"$or": [
            {"features.details.storage.ram": ram_regex},
            {"features.details.Storage.RAM": ram_regex},
            {"title": {"$regex": intent["ram"].replace("GB", "").replace("gb", "").strip() + r"\s*gb\s*ram", "$options": "i"}},
        ]})

    if intent.get("storage"):
        rom_regex = make_regex(intent["storage"])
        and_conditions.append({"$or": [
            {"features.details.storage.rom": rom_regex},
            {"features.details.Storage.ROM": rom_regex},
            {"title": {"$regex": intent["storage"].replace("GB", "").replace("gb", "").strip() + r"\s*gb", "$options": "i"}},
        ]})

    if intent.get("processor"):
        proc_regex = {"$regex": intent["processor"], "$options": "i"}
        and_conditions.append({"$or": [
            {"features.details.performance.processor": proc_regex},
            {"features.details.Performance.processor": proc_regex},
            {"title": proc_regex},
        ]})

    if and_conditions:
        filters["$and"] = and_conditions

    if intent.get("query"):
        filters["title"] = {"$regex": intent["query"], "$options": "i"}

    return filters


def iget(d: dict, key: str, default="") -> str:
    """Case-insensitive dict lookup."""
    key_lower = key.lower()
    for k, v in d.items():
        if k.lower() == key_lower:
            return v or default
    return default


def format_product_summary(products: list) -> str:
    """Serialize only the relevant fields to keep the prompt concise."""
    summaries = []
    for p in products[:5]:
        # Croma wraps product data under a "product" key
        prod = p.get("product", p)

        # Handle price field variants across all scrapers:
        # Flipkart/JioMart/VijaysSales: discounted_price | Amazon/Croma: discounted_Price
        discounted = (
            prod.get("discounted_price")
            or prod.get("discounted_Price")
            or prod.get("price")
            or ""
        )
        original = prod.get("price") or prod.get("actual_price") or ""

        # Handle thumbnail across all scraper schemas
        image_field = prod.get("image") or prod.get("image_url") or {}
        if isinstance(image_field, dict):
            thumbnail = image_field.get("thumbnail", "")
        elif isinstance(image_field, list):
            thumbnail = image_field[0] if image_field else ""
        else:
            thumbnail = str(image_field) if image_field else ""

        # Features: try features.details, then specifications.details (Croma)
        details = prod.get("features", {}).get("details", {}) or {}
        if not details:
            details = prod.get("specifications", {}).get("details", {}) or {}

        storage = iget(details, "storage") or {}
        performance = iget(details, "performance") or {}
        display = iget(details, "display") or {}
        camera = iget(details, "camera") or {}
        battery = iget(details, "battery") or {}

        summary = {
            "title": prod.get("title", "") or prod.get("product_name", ""),
            "brand": prod.get("brand", ""),
            "price": original,
            "discounted_price": discounted,
            "rating": prod.get("rating", ""),
            "thumbnail": thumbnail,
            "offers": prod.get("offers", []),
            "specs": {
                "ram": iget(storage, "ram"),
                "storage": iget(storage, "rom"),
                "processor": iget(performance, "processor"),
                "os": iget(performance, "operating_system") or iget(performance, "operating system"),
                "display": iget(display, "resolution") or iget(display, "screen_resolution") or iget(display, "screen resolution"),
                "rear_camera": iget(camera, "rear_camera") or iget(camera, "rear camera"),
                "front_camera": iget(camera, "front_camera") or iget(camera, "front camera"),
                "battery": iget(battery, "battery_capacity") or iget(battery, "battery capacity"),
                "fast_charging": iget(battery, "fast_charging") or iget(battery, "fast charging"),
            }
        }
        summaries.append(summary)
    return json.dumps(summaries, indent=2)


def generate_chat_response(user_message: str, products: list, conversation_history: list) -> str:
    product_context = format_product_summary(products) if products else "No matching products found."

    messages = [{"role": "system", "content": CHAT_PROMPT}]
    for msg in conversation_history[-6:]:
        messages.append(msg)

    messages.append({
        "role": "user",
        "content": f"Customer question: {user_message}\n\nProduct data from our store:\n{product_context}"
    })

    response = openai_client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=messages,
        temperature=0.7,
        max_tokens=800,
        timeout=15
    )
    return response.choices[0].message.content.strip()


def chat_with_products(user_message: str, conversation_history: list = []) -> dict:
    intent = extract_intent(user_message)
    mongo_filter = build_mongo_filter(intent)

    collection = mongo_client[DB_NAME][COLLECTION_NAME]

    # Determine sort order
    sort_by = intent.get("sort_by")
    if sort_by == "rating":
        cursor = collection.find(mongo_filter).sort("rating", -1).limit(10)
    elif sort_by == "price_asc":
        cursor = collection.find(mongo_filter).sort("discounted_price", 1).limit(10)
    elif sort_by == "price_desc":
        cursor = collection.find(mongo_filter).sort("discounted_price", -1).limit(10)
    else:
        cursor = collection.find(mongo_filter).limit(10)

    products = [convert_objectid(p) for p in cursor]

    # Fallback: title search using query or ram/brand keywords, keeping price filter
    if not products:
        mapped_cat = mongo_filter.get("category")
        fallback_keyword = (
            intent.get("query")
            or intent.get("brand")
            or (intent.get("ram", "").replace("GB", "").replace("gb", "").strip() + " gb ram" if intent.get("ram") else None)
        )
        if fallback_keyword:
            fallback = {"title": {"$regex": fallback_keyword, "$options": "i"}}
            if mapped_cat:
                fallback["category"] = mapped_cat
            if "$expr" in mongo_filter:
                fallback["$expr"] = mongo_filter["$expr"]
            if sort_by == "rating":
                products = [convert_objectid(p) for p in collection.find(fallback).sort("rating", -1).limit(10)]
            else:
                products = [convert_objectid(p) for p in collection.find(fallback).limit(10)]
        # Last resort: price-only search with category
        if not products and "$expr" in mongo_filter:
            last_resort = {"$expr": mongo_filter["$expr"]}
            if mapped_cat:
                last_resort["category"] = mapped_cat
            if sort_by == "rating":
                products = [convert_objectid(p) for p in collection.find(last_resort).sort("rating", -1).limit(10)]
            else:
                products = [convert_objectid(p) for p in collection.find(last_resort).limit(10)]

    chat_response = generate_chat_response(user_message, products, conversation_history)

    return {
        "message": chat_response,
        "products": products,
    }