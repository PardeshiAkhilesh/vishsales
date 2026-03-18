from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    token: str

class Product(BaseModel):
    id: str
    name: str
    price: float
    category: str
    brand: str
    image: str
    description: Optional[str] = None
    rating: Optional[float] = None
    stock: Optional[int] = None

class CartItem(BaseModel):
    product_id: str
    product_name: str
    price: float
    quantity: int
    image: str

class Order(BaseModel):
    user_id: str
    items: List[CartItem]
    total_amount: float
    status: str = "pending"

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str
    phone: Optional[str] = None

class ExchangeRequest(BaseModel):
    user_name: str
    email: EmailStr
    old_product: str
    new_product: str
    phone: str
    address: str

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
