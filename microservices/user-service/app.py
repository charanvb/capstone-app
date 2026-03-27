from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = "user-service-secret-key"

# ==================== IN-MEMORY DATA STRUCTURES ====================

# Store registered users
users = {
    "demo_user": {"password": "demo123", "email": "demo@example.com"},
    "john": {"password": "john123", "email": "john@example.com"}
}

# Store active sessions
sessions = {}


# ==================== HELPER FUNCTIONS ====================

def log_request(method, endpoint, message):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {method} {endpoint} - {message}")


# ==================== ROUTES ====================

@app.route("/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not data.get("username") or not data.get("password") or not data.get("email"):
        log_request("POST", "/register", "Missing required fields")
        return jsonify({"error": "Missing username, password, or email"}), 400
    
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    
    if username in users:
        log_request("POST", "/register", f"Registration failed - user {username} already exists")
        return jsonify({"error": "Username already exists"}), 409
    
    # Register user
    users[username] = {"password": password, "email": email}
    log_request("POST", "/register", f"User {username} registered successfully")
    
    return jsonify({
        "message": "User registered successfully",
        "username": username,
        "email": email
    }), 201


@app.route("/login", methods=["POST"])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data or not data.get("username") or not data.get("password"):
        log_request("POST", "/login", "Missing username or password")
        return jsonify({"error": "Missing username or password"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    # Validate credentials
    if username not in users or users[username]["password"] != password:
        log_request("POST", "/login", f"Login failed for {username}")
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Create session
    session_token = f"session_{username}_{int(datetime.now().timestamp())}"
    sessions[username] = {"logged_in": True, "timestamp": datetime.now().isoformat()}
    
    log_request("POST", "/login", f"User {username} logged in successfully")
    
    return jsonify({
        "message": "Login successful",
        "username": username,
        "session_token": session_token,
        "status": "authenticated"
    }), 200


@app.route("/logout", methods=["POST"])
def logout():
    """Logout user"""
    data = request.get_json()
    
    if not data or not data.get("username"):
        log_request("POST", "/logout", "Missing username")
        return jsonify({"error": "Missing username"}), 400
    
    username = data.get("username")
    
    if username in sessions:
        del sessions[username]
    
    log_request("POST", "/logout", f"User {username} logged out")
    
    return jsonify({
        "message": f"User {username} logged out successfully"
    }), 200


@app.route("/validate", methods=["GET"])
def validate_user():
    """Validate if user is authenticated (internal endpoint for other services)"""
    username = request.headers.get("X-User")
    
    if not username:
        return jsonify({"error": "Missing X-User header"}), 400
    
    if username not in sessions or not sessions[username].get("logged_in"):
        return jsonify({"error": "User not authenticated"}), 401
    
    return jsonify({
        "username": username,
        "authenticated": True
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
    print("USER SERVICE STARTING")
    print("=" * 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server running on http://localhost:5001")
    print("\nAvailable Endpoints:")
    print("  POST /register  - Register a new user")
    print("  POST /login     - Login user")
    print("  POST /logout    - Logout user")
    print("  GET  /validate  - Validate user (internal)")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5001)
