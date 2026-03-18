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


SYSTEM_PROMPT = """You are a smart assistant that extracts structured filters from a user's electronics product query.
Return ONLY a valid JSON object with these optional fields:
{
  "category": "smartphone" | "laptop" | "laptop accessories" | "mobile accessories" | null,
  "brand": "brand name or null",
  "min_price": number or null,
  "max_price": number or null,
  "ram": "e.g. 8gb or null",
  "storage": "e.g. 128gb or null",
  "processor": "e.g. snapdragon or null",
  "query": "short keyword for title search or null",
  "response_message": "a friendly natural language reply to the user"
}
Do not include any explanation outside the JSON."""


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
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0,
        max_tokens=300,
        timeout=10
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


def build_mongo_filter(intent: dict) -> dict:
    filters = {}

    if intent.get("category"):
        filters["category"] = intent["category"].lower()

    if intent.get("brand"):
        filters["brand"] = {"$regex": intent["brand"], "$options": "i"}

    min_p = intent.get("min_price")
    max_p = intent.get("max_price")
    if min_p is not None or max_p is not None:
        filters["discountprice"] = {}
        if min_p is not None:
            filters["discountprice"]["$gte"] = min_p
        if max_p is not None:
            filters["discountprice"]["$lte"] = max_p

    if intent.get("ram"):
        filters["features.details.storage.ram"] = {"$regex": intent["ram"], "$options": "i"}

    if intent.get("storage"):
        filters["features.details.storage.rom"] = {"$regex": intent["storage"], "$options": "i"}

    if intent.get("processor"):
        filters["features.details.performance.processor"] = {"$regex": intent["processor"], "$options": "i"}

    if intent.get("query"):
        filters["title"] = {"$regex": intent["query"], "$options": "i"}

    return filters


def get_similar_products(product: dict, limit: int = 4) -> list:
    collection = mongo_client[DB_NAME][COLLECTION_NAME]
    similar_filter = {}

    if product.get("category"):
        similar_filter["category"] = product["category"]
    if product.get("brand"):
        similar_filter["brand"] = {"$regex": product["brand"], "$options": "i"}
    if product.get("_id"):
        similar_filter["_id"] = {"$ne": product["_id"]}

    results = list(collection.find(similar_filter).limit(limit))
    return [convert_objectid(r) for r in results]


def chat_with_products(user_message: str, conversation_history: list = []) -> dict:
    intent = extract_intent(user_message)
    response_message = intent.pop("response_message", "Here are the products I found for you!")

    mongo_filter = build_mongo_filter(intent)
    collection = mongo_client[DB_NAME][COLLECTION_NAME]

    products = list(collection.find(mongo_filter).limit(10))
    products = [convert_objectid(p) for p in products]

    recommendations = []
    if products:
        recommendations = get_similar_products(products[0], limit=4)

    return {
        "message": response_message,
        "intent": intent,
        "products": products,
        "recommendations": recommendations
    }


def get_chatbot_response(message: str) -> str:
    """Simple chatbot response without OpenAI dependency"""
    message_lower = message.lower()
    
    # Simple keyword-based responses
    if any(word in message_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! I'm here to help you find the perfect products. What are you looking for today?"
    
    if any(word in message_lower for word in ['laptop', 'computer']):
        return "Great! We have a wide range of laptops. Are you looking for gaming laptops, business laptops, or something else?"
    
    if any(word in message_lower for word in ['mobile', 'phone', 'smartphone']):
        return "We have excellent smartphones available! Are you interested in any particular brand like Samsung, Apple, or OnePlus?"
    
    if any(word in message_lower for word in ['price', 'cost', 'budget']):
        return "I can help you find products within your budget. What's your price range?"
    
    if any(word in message_lower for word in ['thank', 'thanks']):
        return "You're welcome! Feel free to ask if you need anything else."
    
    # Default response
    return "I'm here to help you find products! You can ask me about laptops, mobiles, accessories, or any specific brand you're interested in."
