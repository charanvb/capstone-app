from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# ==================== IN-MEMORY DATA STRUCTURES ====================

# Predefined products (prices in INR)
products = [
    {"id": 1, "name": "Gaming Laptop", "price": 79999, "stock": 5, "description": "High-performance laptop for gaming and work", "rating": 4.5, "category": "laptop", "image": "https://images.unsplash.com/photo-1588675521123-456cdc38e58c?w=300&h=300&fit=crop"},
    {"id": 2, "name": "Wireless Mouse", "price": 2499, "stock": 15, "description": "Ergonomic wireless mouse", "rating": 4.5, "category": "accessories", "image": "https://images.unsplash.com/photo-1527814050087-3793815479db?w=300&h=300&fit=crop"},
    {"id": 3, "name": "Mechanical Keyboard", "price": 6999, "stock": 8, "description": "RGB mechanical keyboard with Blue switches", "rating": 4.5, "category": "accessories", "image": "https://images.unsplash.com/photo-1587829191301-4b47ecbe4198?w=300&h=300&fit=crop"},
    {"id": 4, "name": "4K Monitor", "price": 24999, "stock": 3, "description": "4K IPS display 27-inch monitor", "rating": 4.7, "category": "accessories", "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=300&h=300&fit=crop"},
    {"id": 5, "name": "USB-C Cable", "price": 999, "stock": 50, "description": "Fast charging cable (3m)", "rating": 4.3, "category": "accessories", "image": "https://images.unsplash.com/photo-1625948515291-69613efd103f?w=300&h=300&fit=crop"},
    {"id": 6, "name": "Webcam 1080p", "price": 3499, "stock": 12, "description": "Full HD webcam with mic", "rating": 4.4, "category": "accessories", "image": "https://images.unsplash.com/photo-1598866594822-8d4d1d67f8b7?w=300&h=300&fit=crop"},
    {"id": 7, "name": "Headphones", "price": 8999, "stock": 10, "description": "Wireless noise-canceling headphones", "rating": 4.6, "category": "accessories", "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&h=300&fit=crop"},
    {"id": 8, "name": "USB Hub", "price": 1499, "stock": 20, "description": "7-port USB 3.0 hub", "rating": 4.2, "category": "accessories", "image": "https://images.unsplash.com/photo-1625948515291-69613efd103f?w=300&h=300&fit=crop"},
    {"id": 9, "name": "Desk Lamp", "price": 2999, "stock": 7, "description": "LED desk lamp with USB charging", "rating": 4.5, "category": "accessories", "image": "https://images.unsplash.com/photo-1565636192335-14c46fa1120d?w=300&h=300&fit=crop"},
    {"id": 10, "name": "Phone Stand", "price": 599, "stock": 25, "description": "Adjustable phone holder for desk", "rating": 4.1, "category": "accessories", "image": "https://images.unsplash.com/photo-1609034227505-5876f6aa4e90?w=300&h=300&fit=crop"}
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
