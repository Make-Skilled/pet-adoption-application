from flask import Flask, request, render_template, session, redirect, url_for, flash
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Database configuration
try:
    cluster = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
    # Test the connection
    cluster.admin.command('ping')
    db = cluster["petadopt"]
    users = db["users"]
    petdetails = db["petdetails"]  # Fixed: was ["petdetails"]
    requests_collection = db["requests"]  # Fixed: was ["requests"], renamed to avoid conflict
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("⚠️  The app will run but database features won't work.")
    # Create mock objects for development
    users = None
    petdetails = None
    requests_collection = None

app = Flask(__name__)
app.secret_key = "1234567890"  # In production, use a secure random key

# Helper function to validate email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Helper function to validate password strength
def is_strong_password(password):
    return len(password) >= 8

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if database is available
        if users is None:
            flash("Database not available. Please try again later.", "error")
            return render_template("register.html")

        # Get form data
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm-password", "")

        # Validation
        errors = []

        if not name:
            errors.append("Full name is required")
        elif len(name) < 2:
            errors.append("Full name must be at least 2 characters")

        if not email:
            errors.append("Email is required")
        elif not is_valid_email(email):
            errors.append("Please enter a valid email address")
        elif users.find_one({"email": email}):
            errors.append("Email already registered. Please use a different email or login.")

        if not password:
            errors.append("Password is required")
        elif not is_strong_password(password):
            errors.append("Password must be at least 8 characters long")

        if password != confirm_password:
            errors.append("Passwords do not match")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("register.html")

        # Create user
        try:
            hashed_password = generate_password_hash(password)
            user_data = {
                "name": name,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.now(),
                "profile_complete": False
            }

            result = users.insert_one(user_data)

            # Log the user in
            session["user_id"] = str(result.inserted_id)
            session["user_name"] = name
            session["user_email"] = email

            flash("Registration successful! Welcome to PawsHome!", "success")
            return redirect(url_for("home"))

        except Exception as e:
            flash("Registration failed. Please try again.", "error")
            return render_template("register.html")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if database is available
        if users is None:
            flash("Database not available. Please try again later.", "error")
            return render_template("login.html")

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Validation
        if not email or not password:
            flash("Please enter both email and password", "error")
            return render_template("login.html")

        # Find user
        user = users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            # Login successful
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password", "error")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully", "info")
    return redirect(url_for("landing"))

@app.route("/home")
def home():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login to access this page", "error")
        return redirect(url_for("login"))

    # Get filter parameters
    pet_type = request.args.get('type', 'all')
    search_query = request.args.get('search', '')

    # Fetch pets from database
    pets = []
    total_pets = 0

    if petdetails is not None:
        try:
            # Build query
            query = {"status": {"$ne": "adopted"}}  # Don't show adopted pets

            if pet_type != 'all':
                query["pet_type"] = pet_type

            if search_query:
                query["$or"] = [
                    {"name": {"$regex": search_query, "$options": "i"}},
                    {"breed": {"$regex": search_query, "$options": "i"}},
                    {"description": {"$regex": search_query, "$options": "i"}}
                ]

            # Fetch pets with owner information
            pets_cursor = petdetails.find(query).sort("created_at", -1).limit(20)
            pets = list(pets_cursor)
            total_pets = petdetails.count_documents(query)

            # Add owner information to each pet
            for pet in pets:
                if "owner_id" in pet:
                    owner = users.find_one({"_id": ObjectId(pet["owner_id"])})
                    pet["owner_name"] = owner["name"] if owner else "Unknown"
                    pet["owner_email"] = owner["email"] if owner else "Unknown"
                else:
                    pet["owner_name"] = "Unknown"
                    pet["owner_email"] = "Unknown"

        except Exception as e:
            flash("Error loading pets. Please try again.", "error")
            print(f"Error fetching pets: {e}")
    else:
        flash("Database not available. Showing sample data.", "info")
        # Sample data for when database is not available
        pets = [
            {
                "_id": "sample1",
                "name": "Max",
                "pet_type": "dog",
                "breed": "Golden Retriever",
                "age": "young",
                "gender": "male",
                "size": "large",
                "description": "A friendly and energetic dog who loves playing fetch and swimming. Great with kids!",
                "personality": ["friendly", "energetic", "playful"],
                "good_with": ["children", "dogs"],
                "status": "available",
                "owner_name": "Sample Owner",
                "created_at": datetime.now()
            }
        ]
        total_pets = 1

    return render_template("home.html", pets=pets, total_pets=total_pets,
                         current_filter=pet_type, search_query=search_query)

@app.route("/add-pet", methods=["GET", "POST"])
def add_pet():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login to access this page", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        print("🐾 ADD PET: POST request received!")
        print(f"🐾 Form data keys: {list(request.form.keys())}")

        # Check if database is available
        if petdetails is None:
            flash("Database not available. Please try again later.", "error")
            return render_template("addpet.html")

        # Get form data
        pet_data = {
            "name": request.form.get("pet_name", "").strip(),
            "pet_type": request.form.get("pet_type", ""),
            "breed": request.form.get("breed", "").strip(),
            "age": request.form.get("age", ""),
            "gender": request.form.get("gender", ""),
            "size": request.form.get("size", ""),
            "color": request.form.get("color", "").strip(),
            "weight": request.form.get("weight", ""),
            "vaccination_status": request.form.get("vaccination_status", ""),
            "spayed_neutered": request.form.get("spayed_neutered", ""),
            "medical_history": request.form.get("medical_history", "").strip(),
            "personality": request.form.getlist("personality[]"),
            "good_with": request.form.getlist("good_with[]"),
            "special_notes": request.form.get("special_notes", "").strip(),
            "contact_method": request.form.get("contact_method", ""),
            "phone": request.form.get("phone", "").strip(),
            "adoption_fee": request.form.get("adoption_fee", "0"),
            "description": request.form.get("pet_story", "").strip(),
            "owner_id": session["user_id"],
            "status": "available",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        # Validation
        errors = []
        if not pet_data["name"]:
            errors.append("Pet name is required")
        if not pet_data["pet_type"]:
            errors.append("Pet type is required")
        if not pet_data["age"]:
            errors.append("Pet age is required")
        if not pet_data["gender"]:
            errors.append("Pet gender is required")
        if not pet_data["size"]:
            errors.append("Pet size is required")
        if not pet_data["vaccination_status"]:
            errors.append("Vaccination status is required")
        if not pet_data["spayed_neutered"]:
            errors.append("Spayed/neutered status is required")
        if not pet_data["contact_method"]:
            errors.append("Contact method is required")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("addpet.html")

        # Save pet to database
        try:
            result = petdetails.insert_one(pet_data)
            flash("Pet added successfully! Your pet is now available for adoption.", "success")
            return redirect(url_for("home"))
        except Exception as e:
            flash("Failed to add pet. Please try again.", "error")
            print(f"Error adding pet: {e}")
            return render_template("addpet.html")

    return render_template("addpet.html")

@app.route("/my-requests")
def my_requests():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login to access this page", "error")
        return redirect(url_for("login"))

    # Fetch adoption requests for user's pets
    user_requests = []
    stats = {
        "total": 0,
        "pending": 0,
        "approved": 0,
        "rejected": 0
    }

    if requests_collection is not None and petdetails is not None:
        try:
            # Get user's pets
            user_pets = list(petdetails.find({"owner_id": session["user_id"]}))
            pet_ids = [str(pet["_id"]) for pet in user_pets]

            # Get requests for user's pets
            requests_cursor = requests_collection.find({"pet_id": {"$in": pet_ids}}).sort("created_at", -1)
            user_requests = list(requests_cursor)

            # Calculate statistics
            stats["total"] = len(user_requests)
            for req in user_requests:
                if req["status"] in stats:
                    stats[req["status"]] += 1

            # Add pet and requester information
            for req in user_requests:
                # Add pet info
                pet = petdetails.find_one({"_id": ObjectId(req["pet_id"])})
                req["pet_name"] = pet["name"] if pet else "Unknown"
                req["pet_type"] = pet["pet_type"] if pet else "Unknown"

                # Add requester info
                requester = users.find_one({"_id": ObjectId(req["requester_id"])})
                req["requester_name"] = requester["name"] if requester else "Unknown"
                req["requester_email"] = requester["email"] if requester else "Unknown"

        except Exception as e:
            flash("Error loading requests. Please try again.", "error")
            print(f"Error fetching requests: {e}")

    return render_template("requests.html", requests=user_requests, stats=stats)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login to access this page", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        # Handle profile update
        if users is None:
            flash("Database not available. Please try again later.", "error")
            return redirect(url_for("profile"))

        try:
            # Get form data
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            date_of_birth = request.form.get("date_of_birth", "").strip()
            address = request.form.get("address", "").strip()
            bio = request.form.get("bio", "").strip()

            # Validate required fields
            if not name or not email:
                flash("Name and email are required.", "error")
                return redirect(url_for("profile"))

            # Validate email format
            if not is_valid_email(email):
                flash("Please enter a valid email address.", "error")
                return redirect(url_for("profile"))

            # Check if email is already taken by another user
            existing_user = users.find_one({"email": email, "_id": {"$ne": ObjectId(session["user_id"])}})
            if existing_user:
                flash("This email is already registered to another account.", "error")
                return redirect(url_for("profile"))

            # Update user data
            update_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "date_of_birth": date_of_birth,
                "address": address,
                "bio": bio,
                "updated_at": datetime.now()
            }

            result = users.update_one(
                {"_id": ObjectId(session["user_id"])},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                # Update session data
                session["user_name"] = name
                session["user_email"] = email
                flash("Profile updated successfully!", "success")
            else:
                flash("No changes were made to your profile.", "info")

        except Exception as e:
            flash("Error updating profile. Please try again.", "error")
            print(f"Error updating profile: {e}")

        return redirect(url_for("profile"))

    # GET request - fetch user data
    user_data = None
    user_pets_count = 0
    user_requests_count = 0

    if users is not None:
        try:
            # Get user data
            user_data = users.find_one({"_id": ObjectId(session["user_id"])})

            # Get user's pets count
            if petdetails is not None:
                user_pets_count = petdetails.count_documents({"owner_id": session["user_id"]})

            # Get user's requests count (requests they've made)
            if requests_collection is not None:
                user_requests_count = requests_collection.count_documents({"requester_id": session["user_id"]})

        except Exception as e:
            flash("Error loading profile data. Please try again.", "error")
            print(f"Error fetching user data: {e}")

    return render_template("myprofile.html",
                         user=user_data,
                         pets_count=user_pets_count,
                         requests_count=user_requests_count)

@app.route("/change-password", methods=["POST"])
def change_password():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login to access this page", "error")
        return redirect(url_for("login"))

    if users is None:
        flash("Database not available. Please try again later.", "error")
        return redirect(url_for("profile"))

    try:
        # Get form data
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Validate required fields
        if not current_password or not new_password or not confirm_password:
            flash("All password fields are required.", "error")
            return redirect(url_for("profile"))

        # Validate new password strength
        if not is_strong_password(new_password):
            flash("New password must be at least 8 characters long.", "error")
            return redirect(url_for("profile"))

        # Check if new passwords match
        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect(url_for("profile"))

        # Get current user data
        user = users.find_one({"_id": ObjectId(session["user_id"])})
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("profile"))

        # Verify current password
        if not check_password_hash(user["password"], current_password):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("profile"))

        # Update password
        hashed_new_password = generate_password_hash(new_password)
        result = users.update_one(
            {"_id": ObjectId(session["user_id"])},
            {"$set": {"password": hashed_new_password, "updated_at": datetime.now()}}
        )

        if result.modified_count > 0:
            flash("Password changed successfully!", "success")
        else:
            flash("Failed to change password. Please try again.", "error")

    except Exception as e:
        flash("Error changing password. Please try again.", "error")
        print(f"Error changing password: {e}")

    return redirect(url_for("profile"))

@app.route("/request-adoption/<pet_id>", methods=["GET", "POST"])
def request_adoption(pet_id):
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login to request adoption", "error")
        return redirect(url_for("login"))

    # Check if database is available
    if petdetails is None or requests_collection is None:
        flash("Database not available. Please try again later.", "error")
        return redirect(url_for("home"))

    # Get pet details
    try:
        pet = petdetails.find_one({"_id": ObjectId(pet_id)})
        if not pet:
            flash("Pet not found", "error")
            return redirect(url_for("home"))

        # Check if user is trying to adopt their own pet
        if pet["owner_id"] == session["user_id"]:
            flash("You cannot request adoption for your own pet", "error")
            return redirect(url_for("home"))

        # Check if pet is available
        if pet["status"] != "available":
            flash("This pet is no longer available for adoption", "error")
            return redirect(url_for("home"))

        # Check if user has already requested this pet
        existing_request = requests_collection.find_one({
            "pet_id": pet_id,
            "requester_id": session["user_id"],
            "status": {"$in": ["pending", "approved"]}
        })

        if existing_request:
            flash("You have already requested adoption for this pet", "info")
            return redirect(url_for("home"))

    except Exception as e:
        flash("Error processing request", "error")
        print(f"Error in request_adoption: {e}")
        return redirect(url_for("home"))

    if request.method == "POST":
        # Get form data
        message = request.form.get("message", "").strip()
        phone = request.form.get("phone", "").strip()
        experience = request.form.get("experience", "").strip()
        living_situation = request.form.get("living_situation", "").strip()

        # Validation
        if not message:
            flash("Please provide a message explaining why you want to adopt this pet", "error")
            return render_template("request_form.html", pet=pet)

        # Create adoption request
        request_data = {
            "pet_id": pet_id,
            "requester_id": session["user_id"],
            "pet_owner_id": pet["owner_id"],
            "message": message,
            "phone": phone,
            "experience": experience,
            "living_situation": living_situation,
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        try:
            result = requests_collection.insert_one(request_data)
            flash("Adoption request submitted successfully! The pet owner will review your request.", "success")
            return redirect(url_for("home"))
        except Exception as e:
            flash("Failed to submit adoption request. Please try again.", "error")
            print(f"Error creating adoption request: {e}")
            return render_template("request_form.html", pet=pet)

    # GET request - show the request form
    return render_template("request_form.html", pet=pet)

@app.route("/manage-request/<request_id>/<action>", methods=["POST"])
def manage_request(request_id, action):
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login to manage requests", "error")
        return redirect(url_for("login"))

    # Check if database is available
    if requests_collection is None or petdetails is None:
        flash("Database not available. Please try again later.", "error")
        return redirect(url_for("my_requests"))

    try:
        # Get the request
        adoption_request = requests_collection.find_one({"_id": ObjectId(request_id)})
        if not adoption_request:
            flash("Request not found", "error")
            return redirect(url_for("my_requests"))

        # Get the pet to verify ownership
        pet = petdetails.find_one({"_id": ObjectId(adoption_request["pet_id"])})
        if not pet or pet["owner_id"] != session["user_id"]:
            flash("You can only manage requests for your own pets", "error")
            return redirect(url_for("my_requests"))

        # Update request status
        if action == "approve":
            # Approve the request
            requests_collection.update_one(
                {"_id": ObjectId(request_id)},
                {
                    "$set": {
                        "status": "approved",
                        "updated_at": datetime.now()
                    }
                }
            )

            # Update pet status to adopted
            petdetails.update_one(
                {"_id": ObjectId(adoption_request["pet_id"])},
                {
                    "$set": {
                        "status": "adopted",
                        "updated_at": datetime.now()
                    }
                }
            )

            # Reject all other pending requests for this pet
            requests_collection.update_many(
                {
                    "pet_id": adoption_request["pet_id"],
                    "_id": {"$ne": ObjectId(request_id)},
                    "status": "pending"
                },
                {
                    "$set": {
                        "status": "rejected",
                        "updated_at": datetime.now()
                    }
                }
            )

            flash("Adoption request approved! The pet has been marked as adopted.", "success")

        elif action == "reject":
            # Reject the request
            requests_collection.update_one(
                {"_id": ObjectId(request_id)},
                {
                    "$set": {
                        "status": "rejected",
                        "updated_at": datetime.now()
                    }
                }
            )
            flash("Adoption request rejected.", "info")

        else:
            flash("Invalid action", "error")

    except Exception as e:
        flash("Error managing request. Please try again.", "error")
        print(f"Error in manage_request: {e}")

    return redirect(url_for("my_requests"))

@app.route("/my-adoption-requests")
def my_adoption_requests():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login to access this page", "error")
        return redirect(url_for("login"))

    # Fetch adoption requests made by the user
    user_adoption_requests = []
    stats = {
        "total": 0,
        "pending": 0,
        "approved": 0,
        "rejected": 0
    }

    if requests_collection is not None and petdetails is not None:
        try:
            # Get requests made by the user
            requests_cursor = requests_collection.find({"requester_id": session["user_id"]}).sort("created_at", -1)
            user_adoption_requests = list(requests_cursor)

            # Calculate statistics
            stats["total"] = len(user_adoption_requests)
            for req in user_adoption_requests:
                if req["status"] in stats:
                    stats[req["status"]] += 1

            # Add pet and owner information
            for req in user_adoption_requests:
                # Add pet info
                pet = petdetails.find_one({"_id": ObjectId(req["pet_id"])})
                req["pet_name"] = pet["name"] if pet else "Unknown"
                req["pet_type"] = pet["pet_type"] if pet else "Unknown"
                req["pet_breed"] = pet["breed"] if pet and pet.get("breed") else ""
                req["pet_age"] = pet["age"] if pet else "Unknown"
                req["pet_gender"] = pet["gender"] if pet else "Unknown"

                # Add owner info
                owner = users.find_one({"_id": ObjectId(req["pet_owner_id"])})
                req["owner_name"] = owner["name"] if owner else "Unknown"
                req["owner_email"] = owner["email"] if owner else "Unknown"

        except Exception as e:
            flash("Error loading your adoption requests. Please try again.", "error")
            print(f"Error fetching user adoption requests: {e}")

    return render_template("my_adoption_requests.html", requests=user_adoption_requests, stats=stats)

@app.route("/create-sample-data")
def create_sample_data():
    """Create sample pets for testing - only for development"""
    if petdetails is None or users is None:
        flash("Database not available", "error")
        return redirect(url_for("home"))

    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login to access this page", "error")
        return redirect(url_for("login"))

    try:
        # Sample pets data
        sample_pets = [
            {
                "name": "Max",
                "pet_type": "dog",
                "breed": "Golden Retriever",
                "age": "young",
                "gender": "male",
                "size": "large",
                "color": "Golden",
                "weight": "65",
                "vaccination_status": "up-to-date",
                "spayed_neutered": "yes",
                "medical_history": "Healthy, no known issues",
                "personality": ["friendly", "energetic", "playful"],
                "good_with": ["children", "dogs"],
                "special_notes": "Loves playing fetch and swimming",
                "contact_method": "both",
                "phone": "+1-555-0123",
                "adoption_fee": "200",
                "description": "A friendly and energetic dog who loves playing fetch and swimming. Great with kids and other dogs!",
                "owner_id": session["user_id"],
                "status": "available",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "name": "Luna",
                "pet_type": "cat",
                "breed": "Persian",
                "age": "young",
                "gender": "female",
                "size": "medium",
                "color": "White",
                "weight": "8",
                "vaccination_status": "up-to-date",
                "spayed_neutered": "yes",
                "medical_history": "Healthy",
                "personality": ["calm", "cuddly", "independent"],
                "good_with": ["children"],
                "special_notes": "Perfect lap cat, loves quiet spaces",
                "contact_method": "email",
                "phone": "",
                "adoption_fee": "150",
                "description": "A calm and affectionate cat who loves cuddling and quiet spaces. Perfect lap cat!",
                "owner_id": session["user_id"],
                "status": "available",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "name": "Buddy",
                "pet_type": "dog",
                "breed": "Labrador Mix",
                "age": "adult",
                "gender": "male",
                "size": "large",
                "color": "Brown",
                "weight": "70",
                "vaccination_status": "up-to-date",
                "spayed_neutered": "yes",
                "medical_history": "Healthy",
                "personality": ["loyal", "gentle", "playful"],
                "good_with": ["children", "dogs", "cats"],
                "special_notes": "Great family dog",
                "contact_method": "phone",
                "phone": "+1-555-0124",
                "adoption_fee": "180",
                "description": "Loyal and gentle companion who gets along well with other pets and children.",
                "owner_id": session["user_id"],
                "status": "pending",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]

        # Insert sample pets
        result = petdetails.insert_many(sample_pets)
        flash(f"Created {len(result.inserted_ids)} sample pets successfully!", "success")

    except Exception as e:
        flash("Failed to create sample data", "error")
        print(f"Error creating sample data: {e}")

    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(port=5000, debug=True)