#!/usr/bin/env python3

from pymongo import MongoClient
from datetime import datetime
from PIL import Image
import os
import uuid

# Connect to MongoDB
try:
    cluster = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
    cluster.admin.command('ping')
    db = cluster["petadopt"]
    petdetails = db["petdetails"]
    users = db["users"]
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)

# Create a test image
def create_test_image():
    uploads_dir = "static/uploads/pets"
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Create a simple test image
    img = Image.new('RGB', (400, 300), color='green')
    
    # Add some text to make it identifiable
    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        # Try to use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        draw.text((50, 100), "TEST PET", fill='white', font=font)
        draw.text((50, 150), "IMAGE", fill='white', font=font)
    except:
        pass  # If text drawing fails, just use the plain colored image
    
    # Save the image
    unique_filename = f"{uuid.uuid4()}_test_pet.jpg"
    file_path = os.path.join(uploads_dir, unique_filename)
    img.save(file_path)
    
    return f"uploads/pets/{unique_filename}"

# Get a user ID (use the first user in the database)
users_list = list(users.find())
if not users_list:
    print("❌ No users found in database. Please register a user first.")
    exit(1)

user_id = str(users_list[0]["_id"])
user_name = users_list[0]["name"]
print(f"🐾 Using user: {user_name} (ID: {user_id})")

# Create test image
print("🐾 Creating test image...")
image_path = create_test_image()
print(f"✅ Test image created: {image_path}")

# Create test pet data
pet_data = {
    "name": "TestPet",
    "pet_type": "dog",
    "breed": "Test Breed",
    "age": "young",
    "gender": "male",
    "size": "medium",
    "color": "Green",
    "weight": "25",
    "vaccination_status": "up-to-date",
    "spayed_neutered": "yes",
    "medical_history": "Healthy test pet",
    "personality": ["friendly", "playful"],
    "good_with": ["children", "dogs"],
    "special_notes": "This is a test pet with an image",
    "contact_method": "email",
    "phone": "555-TEST",
    "adoption_fee": "50",
    "description": "This is a test pet created to verify image upload functionality",
    "images": [image_path],  # Add the image path
    "owner_id": user_id,
    "owner_name": user_name,
    "status": "available",
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Insert the pet into the database
try:
    result = petdetails.insert_one(pet_data)
    print(f"✅ Test pet added successfully! Pet ID: {result.inserted_id}")
    print(f"🐾 Pet name: {pet_data['name']}")
    print(f"🐾 Image path: {pet_data['images'][0]}")
    print(f"🐾 You should now see this pet with an image on the home page!")
except Exception as e:
    print(f"❌ Failed to add test pet: {e}")
