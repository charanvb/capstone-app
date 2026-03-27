from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime
import requests
import os

app = Flask(__name__)
app.secret_key = "ui-service-secret-key"

# ==================== SERVICE CONFIGURATION ====================
# Service URLs for inter-service communication

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL") or "http://user-service:5001"
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL") or "http://product-service:5002"
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL") or "http://cart-service:5003"
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL") or "http://payment-service:5004"


# ==================== HELPER FUNCTIONS ====================

def log_request(method, endpoint, message):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {method} {endpoint} - {message}")


def call_service(method, url, headers=None, json_data=None):
    """Make HTTP call to microservice with error handling"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=5)
        return response
    except requests.exceptions.RequestException as e:
        log_request(method, url, f"Service call failed: {str(e)}")
        return None


# ==================== ROUTES ====================

@app.route("/", methods=["GET"])
def home():
    """Home page"""
    log_request("GET", "/", "Home page accessed")
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register page and handler"""
    if request.method == "GET":
        log_request("GET", "/register", "Register page accessed")
        return render_template("register.html")
    
    # Handle registration form submission
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    
    if not username or not password or not email:
        flash("All fields are required!", "error")
        return redirect(url_for("register"))
    
    # Call User Service to register
    response = call_service(
        "POST",
        f"{USER_SERVICE_URL}/register",
        json_data={"username": username, "password": password, "email": email}
    )
    
    if response and response.status_code == 201:
        log_request("POST", "/register", f"User {username} registered successfully")
        flash(f"Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    else:
        error_msg = "Username already exists" if response and response.status_code == 409 else "Registration failed"
        flash(error_msg, "error")
        return redirect(url_for("register"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page and handler"""
    if request.method == "GET":
        if session.get("username"):
            return redirect(url_for("shop"))
        log_request("GET", "/login", "Login page accessed")
        return render_template("login.html")
    
    # Handle login form submission
    username = request.form.get("username")
    password = request.form.get("password")
    
    if not username or not password:
        flash("Username and password are required!", "error")
        return redirect(url_for("login"))
    
    # Call User Service to login
    response = call_service(
        "POST",
        f"{USER_SERVICE_URL}/login",
        json_data={"username": username, "password": password}
    )
    
    if response and response.status_code == 200:
        session["username"] = username
        log_request("POST", "/login", f"User {username} logged in")
        flash(f"Welcome {username}!", "success")
        return redirect(url_for("shop"))
    else:
        flash("Invalid username or password", "error")
        return redirect(url_for("login"))


@app.route("/logout", methods=["GET"])
def logout():
    """Logout user"""
    username = session.get("username")
    
    if username:
        # Call User Service to logout
        call_service(
            "POST",
            f"{USER_SERVICE_URL}/logout",
            json_data={"username": username}
        )
        log_request("GET", "/logout", f"User {username} logged out")
        session.clear()
        flash("Logged out successfully", "success")
    
    return redirect(url_for("home"))


@app.route("/shop", methods=["GET"])
def shop():
    """Shop page - display all products"""
    username = session.get("username")
    
    if not username:
        flash("Please login to access shop", "warning")
        return redirect(url_for("login"))
    
    log_request("GET", "/shop", f"Shop page accessed by {username}")
    
    # Call Product Service to get all products
    response = call_service("GET", f"{PRODUCT_SERVICE_URL}/products")
    products = []
    
    if response and response.status_code == 200:
        data = response.json()
        products = data.get("products", [])
        log_request("GET", "/shop", f"Retrieved {len(products)} products")
    
    return render_template("shop.html", products=products, username=username)


@app.route("/cart", methods=["GET"])
def view_cart():
    """View shopping cart"""
    username = session.get("username")
    
    if not username:
        flash("Please login to view cart", "warning")
        return redirect(url_for("login"))
    
    # Call Cart Service to get cart
    response = call_service(
        "GET",
        f"{CART_SERVICE_URL}/cart",
        headers={"X-User": username}
    )
    
    cart_items = []
    cart_total = 0
    
    if response and response.status_code == 200:
        data = response.json()
        cart_items = data.get("items", [])
        cart_total = data.get("cart_total", 0)
        log_request("GET", "/cart", f"Cart retrieved for {username}: {len(cart_items)} items")
    else:
        flash("Error retrieving cart", "error")
    
    return render_template("cart.html", cart_items=cart_items, cart_total=cart_total, username=username)


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    """Add product to cart"""
    username = session.get("username")
    
    if not username:
        flash("Please login first", "warning")
        return redirect(url_for("login"))
    
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", default=1, type=int)
    
    if not product_id or quantity <= 0:
        flash("Invalid product or quantity", "error")
        return redirect(url_for("shop"))
    
    # Call Cart Service to add to cart
    response = call_service(
        "POST",
        f"{CART_SERVICE_URL}/cart/add",
        headers={"X-User": username},
        json_data={"product_id": product_id, "quantity": quantity}
    )
    
    if response and response.status_code == 200:
        data = response.json()
        product_name = data.get("item", {}).get("product_name", "Product")
        flash(f"Added {quantity}x {product_name} to cart", "success")
        log_request("POST", "/add-to-cart", f"User {username} added product {product_id}")
    else:
        flash("Failed to add to cart", "error")
    
    return redirect(url_for("shop"))


@app.route("/checkout", methods=["GET"])
def checkout():
    """Checkout page"""
    username = session.get("username")
    
    if not username:
        flash("Please login to checkout", "warning")
        return redirect(url_for("login"))
    
    # Call Cart Service to get cart
    response = call_service(
        "GET",
        f"{CART_SERVICE_URL}/cart",
        headers={"X-User": username}
    )
    
    if response and response.status_code == 200:
        data = response.json()
        if not data.get("items"):
            flash("Your cart is empty", "warning")
            return redirect(url_for("view_cart"))
        
        return render_template("checkout.html", cart_data=data, username=username)
    else:
        flash("Error retrieving cart", "error")
        return redirect(url_for("view_cart"))


@app.route("/process-payment", methods=["POST"])
def process_payment():
    """Process payment"""
    username = session.get("username")
    
    if not username:
        flash("Please login to checkout", "warning")
        return redirect(url_for("login"))
    
    log_request("POST", "/process-payment", f"Processing payment for {username}")
    
    # Call Payment Service to process payment
    response = call_service(
        "POST",
        f"{PAYMENT_SERVICE_URL}/payment",
        headers={"X-User": username}
    )
    
    if response and response.status_code == 200:
        payment_data = response.json()
        log_request("POST", "/process-payment", f"Payment successful for {username}")
        return render_template(
            "payment-success.html",
            transaction_id=payment_data.get("transaction_id"),
            amount=payment_data.get("amount"),
            username=username
        )
    else:
        flash("Payment failed", "error")
        log_request("POST", "/process-payment", f"Payment failed for {username}")
        return redirect(url_for("view_cart"))


@app.route("/order-history", methods=["GET"])
def order_history():
    """View order/payment history"""
    username = session.get("username")
    
    if not username:
        flash("Please login to view history", "warning")
        return redirect(url_for("login"))
    
    # Call Payment Service to get payment history
    response = call_service(
        "GET",
        f"{PAYMENT_SERVICE_URL}/payment/history",
        headers={"X-User": username}
    )
    
    payment_history = []
    
    if response and response.status_code == 200:
        data = response.json()
        payment_history = data.get("payment_history", [])
        log_request("GET", "/order-history", f"Retrieved {len(payment_history)} orders for {username}")
    
    return render_template("order-history.html", orders=payment_history, username=username)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    log_request("ANY", "UNKNOWN", "Route not found")
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    log_request("ANY", "UNKNOWN", f"Server error: {str(error)}")
    return render_template("500.html"), 500


# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("UI SERVICE STARTING")
    print("=" * 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server running on http://localhost:5000")
    print("\nConnected Services:")
    print(f"  User Service:    {USER_SERVICE_URL}")
    print(f"  Product Service: {PRODUCT_SERVICE_URL}")
    print(f"  Cart Service:    {CART_SERVICE_URL}")
    print(f"  Payment Service: {PAYMENT_SERVICE_URL}")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
