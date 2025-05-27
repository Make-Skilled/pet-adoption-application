#!/usr/bin/env python3

from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
try:
    cluster = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
    cluster.admin.command('ping')
    db = cluster["petadopt"]
    petdetails = db["petdetails"]
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)

# Check existing pets
print("\n🐾 Checking existing pets in database:")
pets = list(petdetails.find())
print(f"Found {len(pets)} pets in database")

for i, pet in enumerate(pets):
    print(f"\nPet {i+1}:")
    print(f"  Name: {pet.get('name', 'N/A')}")
    print(f"  Type: {pet.get('pet_type', 'N/A')}")
    print(f"  Images: {pet.get('images', [])}")
    print(f"  Status: {pet.get('status', 'N/A')}")
    print(f"  Owner ID: {pet.get('owner_id', 'N/A')}")

# Check if there are any images in the uploads folder
import os
uploads_dir = "static/uploads/pets"
if os.path.exists(uploads_dir):
    files = os.listdir(uploads_dir)
    print(f"\n📁 Files in uploads directory: {files}")
else:
    print(f"\n📁 Uploads directory doesn't exist: {uploads_dir}")
