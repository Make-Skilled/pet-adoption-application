#!/usr/bin/env python3

import requests
from io import BytesIO
from PIL import Image
import os

def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (300, 300), color='blue')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_form_submission():
    """Test the actual form submission process"""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("🐾 Step 1: Getting the add pet form page...")
    
    # First, get the add pet page to see if we need to be logged in
    response = session.get("http://127.0.0.1:5000/add-pet")
    print(f"Add pet page response: {response.status_code}")
    print(f"Final URL: {response.url}")
    
    if 'login' in response.url:
        print("🐾 Step 2: Need to login first...")
        
        # Get login page
        login_page = session.get("http://127.0.0.1:5000/login")
        print(f"Login page response: {login_page.status_code}")
        
        # Try to login with existing user
        login_data = {
            'email': 'revanth@example.com',  # Use an existing user
            'password': 'password123'
        }
        
        login_response = session.post("http://127.0.0.1:5000/login", data=login_data)
        print(f"Login response: {login_response.status_code}")
        print(f"Login final URL: {login_response.url}")
        
        if 'login' in login_response.url:
            print("🐾 Login failed, trying with different credentials...")
            # Try with a different user or register
            register_data = {
                'name': 'Test User Form',
                'email': 'testform@example.com',
                'password': 'testpassword123',
                'confirm_password': 'testpassword123'
            }
            register_response = session.post("http://127.0.0.1:5000/register", data=register_data)
            print(f"Register response: {register_response.status_code}")
            print(f"Register final URL: {register_response.url}")
    
    print("🐾 Step 3: Accessing add pet form...")
    
    # Now try to access the add pet form again
    add_pet_response = session.get("http://127.0.0.1:5000/add-pet")
    print(f"Add pet form response: {add_pet_response.status_code}")
    print(f"Add pet form final URL: {add_pet_response.url}")
    
    if 'login' in add_pet_response.url:
        print("❌ Still redirected to login. Authentication issue.")
        return
    
    print("🐾 Step 4: Submitting form with image...")
    
    # Create test image
    test_image1 = create_test_image()
    test_image2 = create_test_image()
    
    # Prepare form data (matching the actual form fields)
    form_data = {
        'pet_name': 'FormTestPet',
        'pet_type': 'dog',
        'breed': 'Form Test Breed',
        'age': 'young',
        'gender': 'male',
        'size': 'medium',
        'color': 'Blue',
        'weight': '35',
        'vaccination_status': 'up-to-date',
        'spayed_neutered': 'yes',
        'medical_history': 'Healthy form test pet',
        'contact_method': 'email',
        'phone': '555-FORM',
        'adoption_fee': '75',
        'pet_story': 'This is a test pet submitted through form to test image upload',
        'terms': 'on'
    }
    
    # Add personality and good_with as arrays (like the form does)
    form_data['personality[]'] = ['friendly', 'playful']
    form_data['good_with[]'] = ['children']
    
    # Prepare files
    files = {
        'photo1': ('test_image1.jpg', test_image1, 'image/jpeg'),
        'photo2': ('test_image2.jpg', test_image2, 'image/jpeg'),
    }
    
    # Submit the form
    submit_response = session.post("http://127.0.0.1:5000/add-pet", data=form_data, files=files)
    
    print(f"Form submission response: {submit_response.status_code}")
    print(f"Form submission final URL: {submit_response.url}")
    
    if submit_response.status_code == 200:
        if 'home' in submit_response.url:
            print("✅ Form submitted successfully! Redirected to home page.")
        else:
            print(f"⚠️  Form submitted but unexpected redirect: {submit_response.url}")
    else:
        print(f"❌ Form submission failed: {submit_response.status_code}")
        print(f"Response content preview: {submit_response.text[:500]}...")

if __name__ == "__main__":
    test_form_submission()
