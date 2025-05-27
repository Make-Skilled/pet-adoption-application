#!/usr/bin/env python3

import requests
from io import BytesIO
from PIL import Image
import os

# Create a simple test image
def create_test_image():
    # Create a simple colored image
    img = Image.new('RGB', (300, 300), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

# Test the upload functionality
def test_upload():
    url = "http://127.0.0.1:5000/add-pet"
    
    # Create test image
    test_image = create_test_image()
    
    # Prepare form data
    form_data = {
        'pet_name': 'Test Pet',
        'pet_type': 'dog',
        'breed': 'Test Breed',
        'age': 'young',
        'gender': 'male',
        'size': 'medium',
        'color': 'Red',
        'weight': '30',
        'vaccination_status': 'up-to-date',
        'spayed_neutered': 'yes',
        'medical_history': 'Healthy',
        'personality[]': ['friendly', 'playful'],
        'good_with[]': ['children'],
        'special_notes': 'Test pet for image upload',
        'contact_method': 'email',
        'phone': '555-1234',
        'adoption_fee': '100',
        'pet_story': 'This is a test pet for image upload functionality',
        'terms': 'on'
    }
    
    # Prepare files
    files = {
        'photo1': ('test_image.jpg', test_image, 'image/jpeg'),
    }
    
    # First, we need to get a session cookie by logging in
    session = requests.Session()
    
    # Try to register/login first
    login_data = {
        'email': 'test@example.com',
        'password': 'testpassword123'
    }
    
    print("🐾 Attempting to login...")
    login_response = session.post("http://127.0.0.1:5000/login", data=login_data)
    print(f"Login response status: {login_response.status_code}")
    
    if login_response.status_code != 200 or 'login' in login_response.url:
        print("🐾 Login failed, trying to register...")
        register_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        }
        register_response = session.post("http://127.0.0.1:5000/register", data=register_data)
        print(f"Register response status: {register_response.status_code}")
    
    # Now try to submit the pet form
    print("🐾 Submitting pet form with image...")
    response = session.post(url, data=form_data, files=files)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response URL: {response.url}")
    
    if response.status_code == 200:
        print("✅ Form submitted successfully!")
    else:
        print(f"❌ Form submission failed: {response.status_code}")
        print(f"Response content: {response.text[:500]}...")

if __name__ == "__main__":
    test_upload()
