from flask import Flask, request, jsonify
from datetime import datetime
import requests
import os

app = Flask(__name__)

# ==================== IN-MEMORY DATA STRUCTURES ====================

# Store shopping carts per user
carts = {}

# ==================== SERVICE CONFIGURATION ====================
# For inter-service communication, we use service names (for Docker/Kubernetes)
# For local development, set these environment variables to use localhost
# Example: set SERVICE_REGISTRY=localhost (Windows) or export SERVICE_REGISTRY=localhost (Linux/Mac)

SERVICE_REGISTRY = os.getenv("SERVICE_REGISTRY", "localhost")  # Default to localhost for local dev
SERVICE_PORT_USER = os.getenv("SERVICE_PORT_USER", "5001")
SERVICE_PORT_PRODUCT = os.getenv("SERVICE_PORT_PRODUCT", "5002")

# Service URLs for inter-service communication
# In Docker/Kubernetes: product-service, user-service (Docker DNS)
# In local dev: localhost (set SERVICE_REGISTRY=localhost)
PRODUCT_SERVICE_URL = f"http://product-service:{SERVICE_PORT_PRODUCT}"
USER_SERVICE_URL = f"http://user-service:{SERVICE_PORT_USER}"

# For local development fallback - try localhost if service name fails
PRODUCT_SERVICE_URL_FALLBACK = f"http://localhost:{SERVICE_PORT_PRODUCT}"
USER_SERVICE_URL_FALLBACK = f"http://localhost:{SERVICE_PORT_USER}"


# ==================== HELPER FUNCTIONS ====================

def log_request(method, endpoint, message):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {method} {endpoint} - {message}")


def get_current_user():
    """Extract current user from request headers"""
    return request.headers.get("X-User")


def validate_user(username):
    """
    Validate if user is authenticated with user-service.
    
    Service Call: GET http://user-service:5001/validate
    Purpose: Verify user authentication before cart operations
    Fallback: If service-name fails, retry with localhost
    """
    try:
        # Try primary URL (service name - for Docker/Kubernetes)
        response = requests.get(
            f"{USER_SERVICE_URL}/validate",
            headers={"X-User": username},
            timeout=2
        )
        if response.status_code == 200:
            log_request("GET", "user-service/validate", f"User {username} validation successful")
            return True
    except requests.exceptions.RequestException as e:
        log_request("GET", "user-service/validate", f"Service name call failed: {str(e)}, trying fallback...")
        
        # Fallback to localhost for local development
        try:
            response = requests.get(
                f"{USER_SERVICE_URL_FALLBACK}/validate",
                headers={"X-User": username},
                timeout=2
            )
            if response.status_code == 200:
                log_request("GET", "user-service/validate (fallback)", f"User {username} validation successful")
                return True
        except requests.exceptions.RequestException as e2:
            log_request("GET", "user-service/validate", f"Both service name and fallback failed: {str(e2)}")
    
    log_request("GET", "user-service/validate", f"User {username} validation failed")
    return False


def get_product(product_id):
    """
    Fetch product details from product-service.
    
    Service Call: GET http://product-service:5002/products/<id>
    Purpose: Retrieve product information and pricing
    Fallback: If service-name fails, retry with localhost
    """
    try:
        # Try primary URL (service name - for Docker/Kubernetes)
        response = requests.get(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}",
            timeout=2
        )
        if response.status_code == 200:
            product = response.json()
            log_request("GET", "product-service/products/<id>", f"Product {product_id} fetched successfully")
            return product
    except requests.exceptions.RequestException as e:
        log_request("GET", "product-service/products/<id>", f"Service name call failed: {str(e)}, trying fallback...")
        
        # Fallback to localhost for local development
        try:
            response = requests.get(
                f"{PRODUCT_SERVICE_URL_FALLBACK}/products/{product_id}",
                timeout=2
            )
            if response.status_code == 200:
                product = response.json()
                log_request("GET", "product-service/products/<id> (fallback)", f"Product {product_id} fetched successfully")
                return product
        except requests.exceptions.RequestException as e2:
            log_request("GET", "product-service/products/<id>", f"Both service name and fallback failed: {str(e2)}")
    
    log_request("GET", "product-service/products/<id>", f"Product {product_id} not found")
    return None


# ==================== ROUTES ====================

@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    """Add product to cart"""
    current_user = get_current_user()
    
    if not current_user:
        log_request("POST", "/cart/add", "No user specified in X-User header")
        return jsonify({"error": "Please login first. Use X-User header with your username"}), 401
    
    # Validate user
    if not validate_user(current_user):
        log_request("POST", "/cart/add", f"User {current_user} not authenticated")
        return jsonify({"error": "User not authenticated"}), 401
    
    data = request.get_json()
    
    if not data or not data.get("product_id") or not data.get("quantity"):
        log_request("POST", "/cart/add", "Missing product_id or quantity")
        return jsonify({"error": "Missing product_id or quantity"}), 400
    
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    
    # Validate quantity
    if not isinstance(quantity, int) or quantity <= 0:
        log_request("POST", "/cart/add", "Invalid quantity")
        return jsonify({"error": "Quantity must be a positive integer"}), 400
    
    # Fetch product from product-service
    product = get_product(product_id)
    if not product:
        log_request("POST", "/cart/add", f"Product {product_id} not found")
        return jsonify({"error": f"Product with id {product_id} not found"}), 404
    
    # Initialize cart if not exists
    if current_user not in carts:
        carts[current_user] = []
    
    # Add to cart
    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "price": product["price"],
        "quantity": quantity,
        "subtotal": product["price"] * quantity
    }
    
    carts[current_user].append(cart_item)
    
    log_request("POST", "/cart/add", f"User {current_user} added {quantity} x {product['name']} to cart")
    
    return jsonify({
        "message": "Product added to cart",
        "item": cart_item,
        "item_count": len(carts[current_user]),
        "cart_total": sum(item["subtotal"] for item in carts[current_user])
    }), 200


@app.route("/cart", methods=["GET"])
def view_cart():
    """View shopping cart"""
    current_user = get_current_user()
    
    if not current_user:
        log_request("GET", "/cart", "No user specified in X-User header")
        return jsonify({"error": "Please login first. Use X-User header with your username"}), 401
    
    # Validate user
    if not validate_user(current_user):
        log_request("GET", "/cart", f"User {current_user} not authenticated")
        return jsonify({"error": "User not authenticated"}), 401
    
    cart = carts.get(current_user, [])
    cart_total = sum(item["subtotal"] for item in cart)
    
    log_request("GET", "/cart", f"User {current_user} viewing cart")
    
    return jsonify({
        "username": current_user,
        "items": cart,
        "item_count": len(cart),
        "cart_total": cart_total
    }), 200


@app.route("/cart/clear", methods=["POST"])
def clear_cart():
    """Clear user's cart (called after payment)"""
    current_user = get_current_user()
    
    if not current_user:
        log_request("POST", "/cart/clear", "No user specified in X-User header")
        return jsonify({"error": "Missing X-User header"}), 400
    
    if current_user in carts:
        carts[current_user] = []
    
    log_request("POST", "/cart/clear", f"Cart cleared for {current_user}")
    
    return jsonify({
        "message": "Cart cleared successfully"
    }), 200


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
    print("CART SERVICE STARTING")
    print("=" * 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server running on http://localhost:5003")
    print("\nAvailable Endpoints:")
    print("  POST /cart/add   - Add product to cart")
    print("  GET  /cart       - View cart")
    print("  POST /cart/clear - Clear cart (internal)")
    print("\nNote: Use 'X-User' header with username for all endpoints")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5003)
