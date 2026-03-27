from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# ==================== IN-MEMORY DATA STRUCTURES ====================

# Predefined products (prices in INR)
products = [
    # Laptops
    {"id": 1, "name": "Gaming Laptop Pro X", "price": 89999, "stock": 5, "description": "High-performance RTX 4060, Intel i7, 16GB RAM, perfect for gaming and work", "rating": 4.8, "category": "Laptops", "image": "https://images.unsplash.com/photo-1588675521123-456cdc38e58c?w=400&h=400&fit=crop"},
    {"id": 2, "name": "Business Ultrabook", "price": 64999, "stock": 8, "description": "Lightweight, long battery life, Intel Core i5, 8GB RAM, perfect for professionals", "rating": 4.6, "category": "Laptops", "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400&h=400&fit=crop"},
    {"id": 3, "name": "MacBook Air M2", "price": 119999, "stock": 3, "description": "Apple M2 chip, 13-inch display, 256GB SSD, stunning aluminum design", "rating": 4.9, "category": "Laptops", "image": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&h=400&fit=crop"},
    
    # Smartphones
    {"id": 4, "name": "Flagship Smartphone 5G", "price": 54999, "stock": 12, "description": "120Hz display, 5G connectivity, 108MP camera, fast charging", "rating": 4.7, "category": "Smartphones", "image": "https://images.unsplash.com/photo-1511707267537-b85faf00021e?w=400&h=400&fit=crop"},
    {"id": 5, "name": "Budget Smartphone", "price": 14999, "stock": 25, "description": "Great value smartphone with 6.5-inch display, decent camera, long battery", "rating": 4.3, "category": "Smartphones", "image": "https://images.unsplash.com/photo-1592286927505-1fed5793f664?w=400&h=400&fit=crop"},
    {"id": 6, "name": "Pro Camera Phone", "price": 79999, "stock": 7, "description": "Triple camera setup, 8K video, AI enhancement, professional photography", "rating": 4.8, "category": "Smartphones", "image": "https://images.unsplash.com/photo-1520275335684-00349f3b76d1?w=400&h=400&fit=crop"},
    
    # Tablets
    {"id": 7, "name": "13-inch Tablet Pro", "price": 49999, "stock": 6, "description": "AMOLED display, stylus support, 128GB storage, great for creativity", "rating": 4.6, "category": "Tablets", "image": "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=400&h=400&fit=crop"},
    {"id": 8, "name": "Basic Tablet", "price": 19999, "stock": 15, "description": "10-inch IPS display, good battery life, perfect for reading and media", "rating": 4.2, "category": "Tablets", "image": "https://images.unsplash.com/photo-1526090881173-8ac2339960e0?w=400&h=400&fit=crop"},
    
    # Headphones & Audio
    {"id": 9, "name": "Wireless Earbuds Pro", "price": 12999, "stock": 18, "description": "Active noise cancellation, 30hr battery with case, premium sound", "rating": 4.7, "category": "Audio", "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop"},
    {"id": 10, "name": "Over-Ear Headphones", "price": 18999, "stock": 10, "description": "Studio quality sound, comfortable fit, 40hr battery life", "rating": 4.8, "category": "Audio", "image": "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=400&h=400&fit=crop"},
    {"id": 11, "name": "Budget Earbuds", "price": 3999, "stock": 30, "description": "Great sound quality for the price, IPX4 water resistant", "rating": 4.1, "category": "Audio", "image": "https://images.unsplash.com/photo-1487215078519-e21cc028cb29?w=400&h=400&fit=crop"},
    
    # Monitors & Displays
    {"id": 12, "name": "4K Gaming Monitor 32\"", "price": 34999, "stock": 4, "description": "4K UHD, 144Hz refresh, HDR support, perfect for gaming", "rating": 4.7, "category": "Monitors", "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400&h=400&fit=crop"},
    {"id": 13, "name": "Ultrawide Monitor 34\"", "price": 44999, "stock": 3, "description": "21:9 aspect ratio, 100Hz, curved display for immersive experience", "rating": 4.6, "category": "Monitors", "image": "https://images.unsplash.com/photo-1611532736579-6b16e2b50449?w=400&h=400&fit=crop"},
    
    # Keyboards
    {"id": 14, "name": "Mechanical Gaming Keyboard", "price": 8999, "stock": 12, "description": "RGB switches, programmable keys, aluminum frame, Blue switches", "rating": 4.6, "category": "Accessories", "image": "https://images.unsplash.com/photo-1587829191301-4b47ecbe4198?w=400&h=400&fit=crop"},
    {"id": 15, "name": "Wireless Office Keyboard", "price": 3999, "stock": 20, "description": "Silent mechanical switches, rechargeable, compact design", "rating": 4.3, "category": "Accessories", "image": "https://images.unsplash.com/photo-1604522442556-989682d8a2ae?w=400&h=400&fit=crop"},
    
    # Mouse
    {"id": 16, "name": "Gaming Mouse with Pad", "price": 4999, "stock": 18, "description": "16000 DPI sensor, programmable buttons, mouse pad included", "rating": 4.5, "category": "Accessories", "image": "https://images.unsplash.com/photo-1527814050087-3793815479db?w=400&h=400&fit=crop"},
    {"id": 17, "name": "Ergonomic Wireless Mouse", "price": 2999, "stock": 22, "description": "Ergonomic design, 2.4GHz wireless, silent clicking", "rating": 4.4, "category": "Accessories", "image": "https://images.unsplash.com/photo-1586253408387-4953da29bdf8?w=400&h=400&fit=crop"},
    
    # Webcams
    {"id": 18, "name": "4K Pro Webcam", "price": 7999, "stock": 9, "description": "Ultra HD 4K resolution, wide-angle lens, built-in microphone", "rating": 4.6, "category": "Accessories", "image": "https://images.unsplash.com/photo-1598866594822-8d4d1d67f8b7?w=400&h=400&fit=crop"},
    {"id": 19, "name": "1080p Compact Webcam", "price": 2999, "stock": 16, "description": "Full HD, auto-focus, great for video calls and streaming", "rating": 4.2, "category": "Accessories", "image": "https://images.unsplash.com/photo-1596933248140-ddc8e20b1bae?w=400&h=400&fit=crop"},
    
    # Cables & Chargers
    {"id": 20, "name": "Fast USB-C Charger 65W", "price": 1999, "stock": 35, "description": "USB-C Power Delivery charging, dual port, 65W output", "rating": 4.5, "category": "Accessories", "image": "https://images.unsplash.com/photo-1625948515291-69613efd103f?w=400&h=400&fit=crop"},
    {"id": 21, "name": "Premium USB-C Cable 3m", "price": 799, "stock": 50, "description": "Fast charging cable, durable braided design, supports 100W", "rating": 4.3, "category": "Accessories", "image": "https://images.unsplash.com/photo-1625948515291-69613efd103f?w=400&h=400&fit=crop"},
    
    # Desk Accessories
    {"id": 22, "name": "Smart LED Desk Lamp", "price": 3999, "stock": 14, "description": "Adjustable brightness, USB charging port, touch control", "rating": 4.4, "category": "Accessories", "image": "https://images.unsplash.com/photo-1565636192335-14c46fa1120d?w=400&h=400&fit=crop"},
    {"id": 23, "name": "Phone & Tablet Stand", "price": 1299, "stock": 28, "description": "Adjustable height, aluminum construction, supports all devices", "rating": 4.2, "category": "Accessories", "image": "https://images.unsplash.com/photo-1609034227505-5876f6aa4e90?w=400&h=400&fit=crop"},
    {"id": 24, "name": "Monitor Arm Stand", "price": 6999, "stock": 8, "description": "Dual monitor support, full adjustability, premium steel construction", "rating": 4.7, "category": "Accessories", "image": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=400&h=400&fit=crop"},
    
    # Storage
    {"id": 25, "name": "1TB Portable SSD", "price": 9999, "stock": 12, "description": "Fast 1050MB/s, compact size, USB-C connection", "rating": 4.6, "category": "Storage", "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400&h=400&fit=crop"},
    {"id": 26, "name": "2TB External HDD", "price": 4999, "stock": 20, "description": "Large storage, USB 3.0, portable hard drive", "rating": 4.3, "category": "Storage", "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400&h=400&fit=crop"},
    
    # Smartwatches
    {"id": 27, "name": "Smartwatch Pro", "price": 24999, "stock": 10, "description": "AMOLED display, heart rate monitor, GPS, 5-day battery", "rating": 4.7, "category": "Wearables", "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop"},
    {"id": 28, "name": "Basic Fitness Band", "price": 5999, "stock": 18, "description": "Activity tracking, heart rate, waterproof, 10-day battery", "rating": 4.2, "category": "Wearables", "image": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400&h=400&fit=crop"},
    
    # Portable Speakers
    {"id": 29, "name": "Bluetooth Speaker Pro", "price": 8999, "stock": 14, "description": "360° sound, waterproof, 24hr battery, deep bass", "rating": 4.6, "category": "Audio", "image": "https://images.unsplash.com/photo-1589003077984-894e133814c9?w=400&h=400&fit=crop"},
    {"id": 30, "name": "Portable Mini Speaker", "price": 2999, "stock": 26, "description": "Compact size, 12hr battery, waterproof, pocket-friendly", "rating": 4.1, "category": "Audio", "image": "https://images.unsplash.com/photo-1589003077984-894e133814c9?w=400&h=400&fit=crop"},
]


# ==================== HELPER FUNCTIONS ====================

def log_request(method, endpoint, message):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {method} {endpoint} - {message}")


# ==================== ROUTES ====================

@app.route("/products", methods=["GET"])
def get_products():
    """Get all products"""
    log_request("GET", "/products", f"Fetching all {len(products)} products")
    return jsonify({
        "total_products": len(products),
        "products": products
    }), 200


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Get a specific product by ID"""
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        log_request("GET", f"/products/{product_id}", "Product not found")
        return jsonify({"error": f"Product with id {product_id} not found"}), 404
    
    log_request("GET", f"/products/{product_id}", "Product found")
    return jsonify(product), 200


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    log_request("ANY", "UNKNOWN", "Route not found")
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    log_request("ANY", "UNKNOWN", f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("PRODUCT SERVICE STARTING")
    print("=" * 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server running on http://localhost:5002")
    print("\nAvailable Endpoints:")
    print("  GET /products        - Get all products")
    print("  GET /products/<id>   - Get specific product")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5002)
