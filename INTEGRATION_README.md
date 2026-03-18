# Vishal Sales - E-Commerce Platform

Full-stack e-commerce application with FastAPI backend and HTML/CSS/JS frontend.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (running on localhost:27017)
- Modern web browser

### Installation & Setup

1. **Install Python dependencies:**
```bash
cd backend
pip install -r app/requirements.txt
```

2. **Configure environment variables:**
Edit `backend/.env` file with your settings:
```env
MONGO_URI=mongodb://localhost:27017
SECRET_KEY=vishal_sales_super_secret_key_2024
MONGO_DB=vishal_sales
```

3. **Seed the database (run once):**
```bash
cd backend
python seed.py
```

4. **Start the backend server:**
```bash
# Windows
cd vishal_sales
start.bat

# Or manually:
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

5. **Open the frontend:**
- Use VS Code Live Server on `frontend/index.html`
- Or open `frontend/index.html` directly in browser
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
vishal_sales/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── requirements.txt     # Python dependencies
│   │   ├── database/
│   │   │   └── mongo.py         # MongoDB connection
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   └── services/
│   │       ├── routes.py        # API routes
│   │       ├── task.py          # Utility functions
│   │       └── chatbot.py       # Chatbot service
│   ├── .env                     # Environment variables
│   └── seed.py                  # Database seeder
├── frontend/
│   ├── js/
│   │   └── api.js               # API helper functions
│   ├── index.html               # Home page
│   ├── login.html               # Login page
│   ├── register.html            # Registration page
│   ├── contact.html             # Contact page
│   └── ...                      # Other pages
└── start.bat                    # Windows startup script
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user profile

### Products
- `GET /api/products` - Get all products
- `GET /api/products/{id}` - Get product by ID
- `GET /api/products/category/{category}` - Get products by category
- `GET /api/products/search?q={query}` - Search products

### Cart
- `GET /api/cart` - Get user's cart
- `POST /api/cart` - Add item to cart
- `DELETE /api/cart/{item_id}` - Remove item from cart

### Orders
- `POST /api/orders` - Create new order
- `GET /api/orders` - Get user's orders

### Contact & Exchange
- `POST /api/contact` - Submit contact form
- `POST /api/exchange` - Submit exchange request

### Chatbot
- `POST /api/chatbot` - Send message to chatbot

### Brands
- `GET /api/brands` - Get all brands

## 🔐 Authentication

The application uses JWT tokens for authentication:
1. Register or login to receive a token
2. Token is stored in localStorage as `vishal_token`
3. Token is automatically included in API requests via `api.js`

## 🛠️ Development

### Backend Development
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Development
Use VS Code Live Server extension or any static file server.

### Database Management
- MongoDB Compass: mongodb://localhost:27017
- Database name: `vishal_sales`
- Collections: users, products, cart, orders, contacts, exchanges

## 📝 Features

- ✅ User authentication (register/login)
- ✅ Product browsing by category
- ✅ Product search
- ✅ Shopping cart management
- ✅ Order placement
- ✅ Contact form
- ✅ Product exchange requests
- ✅ AI Chatbot for product recommendations
- ✅ Responsive design

## 🐛 Troubleshooting

**MongoDB Connection Error:**
- Ensure MongoDB is running: `mongod`
- Check MONGO_URI in `.env` file

**CORS Error:**
- Backend allows all origins by default
- Check API_BASE_URL in `frontend/js/api.js`

**Import Errors:**
- Reinstall dependencies: `pip install -r app/requirements.txt`

## 📄 License

This project is for educational purposes.
