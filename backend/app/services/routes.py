import json
from typing import List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
import os
from datetime import datetime

from database.mongo import client as mongo_client, get_db
from services.chatbot import chat_with_products
from models.schemas import *
from services.task import hash_password, verify_password, create_token, decode_token

load_dotenv()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

DB_NAME = os.getenv("MONGO_DB", "vishal_sales")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ecommerce_data")


# Convert ObjectId to string
def convert_objectid(document):
    if isinstance(document, dict):
        return {k: convert_objectid(v) for k, v in document.items()}
    elif isinstance(document, list):
        return [convert_objectid(item) for item in document]
    elif isinstance(document, ObjectId):
        return str(document)
    return document

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


class PaginatedResponse(BaseModel):
    status: str
    total_items: int
    page: int
    limit: int
    total_pages: int
    data: List[Any]


@router.get("/")
def read_root():
    return {"message": "Welcome to the E-commerce API!"}


@router.get("/productlisting")
def product_listing(
    category: Optional[str] = "",
    brand: Optional[str] = "",
    minPrice: Optional[float] = 0,
    maxPrice: Optional[float] = None,
    features: Optional[str] = "",
    query: Optional[str] = "",
    page: int = 1,
    limit: int = 24,
    sortby: int = -1
):
    try:
        collection = mongo_client[DB_NAME][COLLECTION_NAME]
        match_conditions = {}

        # Category filter
        if category:
            match_conditions["category"] = category.lower()

        # Brand filter
        if brand:
            match_conditions["brand"] = {
                "$in": [b.strip().lower() for b in brand.split(",")]
            }

        # Price filter
        if minPrice > 0 or maxPrice is not None:
            price_filter = {}
            if minPrice > 0:
                price_filter["$gte"] = minPrice
            if maxPrice is not None:
                price_filter["$lte"] = maxPrice
            if price_filter:
                match_conditions["discountprice"] = price_filter

        # Text search
        if query:
            match_conditions["$or"] = [
                {"title": {"$regex": query, "$options": "i"}}
            ]

        # Features filter
        try:
            features_dict = json.loads(features) if features else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid features JSON format")

        if category:
            category = category.lower()

            if category == "smartphone":
                if "processor" in features_dict:
                    match_conditions["features.details.performance.processor"] = {
                        "$in": features_dict["processor"]
                    }

                if "ram" in features_dict:
                    match_conditions["features.details.storage.ram"] = {
                        "$in": features_dict["ram"]
                    }

                if "storage" in features_dict:
                    match_conditions["features.details.storage.rom"] = {
                        "$in": features_dict["storage"]
                    }

                if "operatingSystem" in features_dict:
                    match_conditions["features.details.performance.operating_system"] = {
                        "$in": features_dict["operatingSystem"]
                    }

            elif category == "laptop":
                if "processor" in features_dict:
                    match_conditions["features.details.performance.processor"] = {
                        "$in": features_dict["processor"]
                    }

                if "ram" in features_dict:
                    match_conditions["features.details.storage.ram"] = {
                        "$in": features_dict["ram"]
                    }

                if "storage" in features_dict:
                    match_conditions["features.details.storage.rom"] = {
                        "$in": features_dict["storage"]
                    }

        # Pagination
        skip = (page - 1) * limit

        # Query MongoDB
        cursor = collection.find(match_conditions).sort("discountprice", sortby)

        total_count = collection.count_documents(match_conditions)

        results = list(cursor.skip(skip).limit(limit))

        results = convert_objectid(results)

        return {
            "status": "success",
            "total_items": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit,
            "products": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product/{mongo_id}")
def get_product(mongo_id: str):

    try:
        obj_id = ObjectId(mongo_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    collection = mongo_client[DB_NAME][COLLECTION_NAME]

    product = collection.find_one({
        "_id": obj_id,
        "image.thumbnail": {"$exists": True, "$ne": ""}
    })

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product = convert_objectid(product)

    return JSONResponse(content=product)


@router.get("/filters")
def get_filters():
    return {
        "categories": [
            "laptop",
            "laptop accessories",
            "smartphone",
            "mobile accessories"
        ],
        "sortoptions": [
            "Price: Low to High",
            "Price: High to Low"
        ],
        "pricerange": {
            "min": 199,
            "max": 199900
        }
    }


class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        result = chat_with_products(request.message, request.history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── AUTH ROUTES ────────────────────────────────────────────────
@router.post("/auth/register", status_code=201)
async def register(user: UserRegister):
    db = get_db()
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(user.password)
    new_user = {"name": user.name, "email": user.email, 
                "password": hashed, "phone": user.phone, 
                "created_at": datetime.now()}
    result = db.users.insert_one(new_user)
    token = create_token({"id": str(result.inserted_id), "email": user.email})
    return {"message": "Registered successfully", "token": token, 
            "user": {"id": str(result.inserted_id), "name": user.name, "email": user.email}}

@router.post("/auth/login")
async def login(user: UserLogin):
    db = get_db()
    found = db.users.find_one({"email": user.email})
    if not found or not verify_password(user.password, found["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token({"id": str(found["_id"]), "email": found["email"]})
    return {"message": "Login successful", "token": token,
            "user": {"id": str(found["_id"]), "name": found["name"], "email": found["email"]}}

@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(current_user["id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"], 
            "phone": user.get("phone")}


# ─── PRODUCT ROUTES ─────────────────────────────────────────────
@router.get("/products")
async def get_products(category: str = None, brand: str = None, limit: int = 50, skip: int = 0):
    db = get_db()
    query = {}
    if category: query["category"] = {"$regex": category, "$options": "i"}
    if brand: query["brand"] = {"$regex": brand, "$options": "i"}
    products = list(db.products.find(query).skip(skip).limit(limit))
    for p in products: p["_id"] = str(p["_id"])
    return {"products": products, "total": db.products.count_documents(query)}

@router.get("/products/search")
async def search_products(q: str):
    db = get_db()
    results = list(db.products.find({
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"brand": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}}
        ]
    }).limit(20))
    for r in results: r["_id"] = str(r["_id"])
    return {"results": results}

@router.get("/products/category/{category}")
async def get_by_category(category: str):
    db = get_db()
    products = list(db.products.find({"category": {"$regex": category, "$options": "i"}}))
    for p in products: p["_id"] = str(p["_id"])
    return {"category": category, "products": products}

@router.get("/products/{product_id}")
async def get_product(product_id: str):
    db = get_db()
    try:
        product = db.products.find_one({"_id": ObjectId(product_id)})
    except:
        product = db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["_id"] = str(product["_id"])
    return product


# ─── CART ROUTES ────────────────────────────────────────────────
@router.get("/cart")
async def get_cart(current_user: dict = Depends(get_current_user)):
    db = get_db()
    cart = list(db.cart.find({"user_id": current_user["id"]}))
    for item in cart: item["_id"] = str(item["_id"])
    return {"cart": cart}

@router.post("/cart")
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    db = get_db()
    existing = db.cart.find_one({"user_id": current_user["id"], "product_id": item.product_id})
    if existing:
        db.cart.update_one({"_id": existing["_id"]}, 
                           {"$inc": {"quantity": item.quantity}})
        return {"message": "Cart updated"}
    cart_item = item.dict()
    cart_item["user_id"] = current_user["id"]
    db.cart.insert_one(cart_item)
    return {"message": "Item added to cart"}

@router.put("/cart/{item_id}")
async def update_cart(item_id: str, quantity: int, current_user: dict = Depends(get_current_user)):
    db = get_db()
    db.cart.update_one({"_id": ObjectId(item_id), "user_id": current_user["id"]}, 
                       {"$set": {"quantity": quantity}})
    return {"message": "Cart updated"}

@router.delete("/cart/{item_id}")
async def remove_from_cart(item_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    db.cart.delete_one({"_id": ObjectId(item_id), "user_id": current_user["id"]})
    return {"message": "Item removed"}

@router.delete("/cart")
async def clear_cart(current_user: dict = Depends(get_current_user)):
    db = get_db()
    db.cart.delete_many({"user_id": current_user["id"]})
    return {"message": "Cart cleared"}


# ─── ORDER ROUTES ───────────────────────────────────────────────
@router.post("/orders")
async def create_order(order: Order, current_user: dict = Depends(get_current_user)):
    db = get_db()
    order_data = order.dict()
    order_data["user_id"] = current_user["id"]
    order_data["created_at"] = datetime.now()
    result = db.orders.insert_one(order_data)
    db.cart.delete_many({"user_id": current_user["id"]})
    return {"message": "Order placed", "order_id": str(result.inserted_id)}

@router.get("/orders")
async def get_orders(current_user: dict = Depends(get_current_user)):
    db = get_db()
    orders = list(db.orders.find({"user_id": current_user["id"]}))
    for o in orders: o["_id"] = str(o["_id"])
    return {"orders": orders}


# ─── CONTACT ROUTE ──────────────────────────────────────────────
@router.post("/contact")
async def submit_contact(form: ContactForm):
    db = get_db()
    data = form.dict()
    data["submitted_at"] = datetime.now()
    db.contacts.insert_one(data)
    return {"message": "Thank you! We'll get back to you soon."}


# ─── EXCHANGE ROUTE ─────────────────────────────────────────────
@router.post("/exchange")
async def submit_exchange(request: ExchangeRequest):
    db = get_db()
    data = request.dict()
    data["status"] = "pending"
    data["submitted_at"] = datetime.now()
    db.exchanges.insert_one(data)
    return {"message": "Exchange request submitted successfully!"}


# ─── CHATBOT ROUTE ──────────────────────────────────────────────
@router.post("/chatbot")
async def chatbot(msg: ChatMessage):
    from services.chatbot import get_chatbot_response
    # Simple fallback if chatbot service doesn't have get_chatbot_response
    try:
        response = get_chatbot_response(msg.message)
    except:
        # Use existing chat_with_products as fallback
        result = chat_with_products(msg.message, [])
        response = result.get("message", "I'm here to help you find products!")
    return {"reply": response}


# ─── BRANDS & DATA ROUTES ───────────────────────────────────────
@router.get("/brands")
async def get_brands():
    db = get_db()
    brands = db.products.distinct("brand")
    return {"brands": brands}

@router.get("/data/flipkart")
async def get_flipkart_data():
    json_path = os.path.join(os.path.dirname(__file__), "../../../flipkart_products.json")
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        return {"products": data}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data file not found")