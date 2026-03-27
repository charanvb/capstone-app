from flask import Flask, request, jsonify
from datetime import datetime
import requests
import os

app = Flask(__name__)

# ==================== SERVICE CONFIGURATION ====================
# For inter-service communication, we use service names (for Docker/Kubernetes)
# For local development, set these environment variables to use localhost
# Example: set SERVICE_REGISTRY=localhost (Windows) or export SERVICE_REGISTRY=localhost (Linux/Mac)

SERVICE_REGISTRY = os.getenv("SERVICE_REGISTRY", "localhost")  # Default to localhost for local dev
SERVICE_PORT_CART = os.getenv("SERVICE_PORT_CART", "5003")
SERVICE_PORT_USER = os.getenv("SERVICE_PORT_USER", "5001")

# Service URLs for inter-service communication
# In Docker/Kubernetes: cart-service, user-service (Docker DNS)
# In local dev: localhost (set SERVICE_REGISTRY=localhost)
CART_SERVICE_URL = f"http://cart-service:{SERVICE_PORT_CART}"
USER_SERVICE_URL = f"http://user-service:{SERVICE_PORT_USER}"

# For local development fallback - try localhost if service name fails
CART_SERVICE_URL_FALLBACK = f"http://localhost:{SERVICE_PORT_CART}"
USER_SERVICE_URL_FALLBACK = f"http://localhost:{SERVICE_PORT_USER}"

# Store payment history
payment_history = {}


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
    Purpose: Verify user authentication before processing payment
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


def get_user_cart(username):
    """
    Fetch user's cart from cart-service.
    
    Service Call: GET http://cart-service:5003/cart
    Purpose: Retrieve cart items and total before payment
    Fallback: If service-name fails, retry with localhost
    """
    try:
        # Try primary URL (service name - for Docker/Kubernetes)
        response = requests.get(
            f"{CART_SERVICE_URL}/cart",
            headers={"X-User": username},
            timeout=2
        )
        if response.status_code == 200:
            log_request("GET", "cart-service/cart", f"Cart fetched for user {username}")
            return response.json()
    except requests.exceptions.RequestException as e:
        log_request("GET", "cart-service/cart", f"Service name call failed: {str(e)}, trying fallback...")
        
        # Fallback to localhost for local development
        try:
            response = requests.get(
                f"{CART_SERVICE_URL_FALLBACK}/cart",
                headers={"X-User": username},
                timeout=2
            )
            if response.status_code == 200:
                log_request("GET", "cart-service/cart (fallback)", f"Cart fetched for user {username}")
                return response.json()
        except requests.exceptions.RequestException as e2:
            log_request("GET", "cart-service/cart", f"Both service name and fallback failed: {str(e2)}")
    
    log_request("GET", "cart-service/cart", f"Failed to fetch cart for user {username}")
    return None


def clear_user_cart(username):
    """
    Clear user's cart after successful payment.
    
    Service Call: POST http://cart-service:5003/cart/clear
    Purpose: Reset cart after payment is processed
    Fallback: If service-name fails, retry with localhost
    """
    try:
        # Try primary URL (service name - for Docker/Kubernetes)
        response = requests.post(
            f"{CART_SERVICE_URL}/cart/clear",
            headers={"X-User": username},
            timeout=2
        )
        if response.status_code == 200:
            log_request("POST", "cart-service/cart/clear", f"Cart cleared for user {username}")
            return True
    except requests.exceptions.RequestException as e:
        log_request("POST", "cart-service/cart/clear", f"Service name call failed: {str(e)}, trying fallback...")
        
        # Fallback to localhost for local development
        try:
            response = requests.post(
                f"{CART_SERVICE_URL_FALLBACK}/cart/clear",
                headers={"X-User": username},
                timeout=2
            )
            if response.status_code == 200:
                log_request("POST", "cart-service/cart/clear (fallback)", f"Cart cleared for user {username}")
                return True
        except requests.exceptions.RequestException as e2:
            log_request("POST", "cart-service/cart/clear", f"Both service name and fallback failed: {str(e2)}")
    
    log_request("POST", "cart-service/cart/clear", f"Failed to clear cart for user {username}")
    return False


# ==================== ROUTES ====================

@app.route("/payment", methods=["POST"])
def process_payment():
    """Process payment for user's cart"""
    current_user = get_current_user()
    
    if not current_user:
        log_request("POST", "/payment", "No user specified in X-User header")
        return jsonify({"error": "Please login first. Use X-User header with your username"}), 401
    
    # Validate user
    if not validate_user(current_user):
        log_request("POST", "/payment", f"User {current_user} not authenticated")
        return jsonify({"error": "User not authenticated"}), 401
    
    # Fetch user's cart
    cart_data = get_user_cart(current_user)
    if not cart_data:
        log_request("POST", "/payment", f"Could not fetch cart for {current_user}")
        return jsonify({"error": "Could not retrieve cart"}), 500
    
    cart_items = cart_data.get("items", [])
    
    if not cart_items:
        log_request("POST", "/payment", f"User {current_user} attempted payment with empty cart")
        return jsonify({"error": "Cart is empty"}), 400
    
    total_amount = cart_data.get("cart_total", 0)
    
    # Mock payment - always succeeds
    transaction_id = f"TXN_{current_user}_{int(datetime.now().timestamp())}"
    
    log_request("POST", "/payment", f"Payment processed for {current_user} - Amount: ₹{total_amount} - TXN: {transaction_id}")
    
    # Store payment history
    if current_user not in payment_history:
        payment_history[current_user] = []
    
    payment_history[current_user].append({
        "transaction_id": transaction_id,
        "amount": total_amount,
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "items": cart_items
    })
    
    # Clear cart after successful payment
    clear_user_cart(current_user)
    
    return jsonify({
        "message": "Payment successful",
        "transaction_id": transaction_id,
        "username": current_user,
        "amount": total_amount,
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/payment/history", methods=["GET"])
def get_payment_history():
    """Get payment history for user (internal endpoint)"""
    current_user = get_current_user()
    
    if not current_user:
        log_request("GET", "/payment/history", "No user specified in X-User header")
        return jsonify({"error": "Missing X-User header"}), 400
    
    history = payment_history.get(current_user, [])
    
    log_request("GET", "/payment/history", f"Retrieved {len(history)} payments for {current_user}")
    
    return jsonify({
        "username": current_user,
        "total_payments": len(history),
        "payment_history": history
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
    print("PAYMENT SERVICE STARTING")
    print("=" * 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server running on http://localhost:5004")
    print("\nAvailable Endpoints:")
    print("  POST /payment          - Process payment")
    print("  GET  /payment/history  - Get payment history (internal)")
    print("\nNote: Use 'X-User' header with username for all endpoints")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5004)
